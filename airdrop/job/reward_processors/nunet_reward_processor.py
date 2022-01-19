
import math

from decimal import Decimal
from common.exception_handler import exception_handler
from airdrop.config import SLACK_HOOK
from common.logger import get_logger

logger = get_logger(__name__)

TOKENS_ALLOCATED_PER_WINDOW = Decimal(12500000)
SCORE_DENOMINATOR = Decimal(100000)
NUNET_DECIMALS = Decimal(1000000)
AGIX_DECIMALS = Decimal(100000000)
AGIX_THRESHOLD_IN_COGS = 250000000000

class UserRewardObject:
    def __init__(self, address, balance, staked):
        self._address = address
        self._balance = Decimal(balance) / AGIX_DECIMALS
        self._staked = Decimal(staked) / AGIX_DECIMALS
        self._score = round((self._balance + (Decimal(0.2) * self._staked)) / SCORE_DENOMINATOR, 6)
        self._log10_score = round(Decimal(math.log10(self._score + 1)),6)
        self._reward = 0
        self._comment = None

    def set_comment(self, comment):
        self._comment = comment
    
    def set_reward(self, reward):
        self._reward = reward


class NunetRewardProcessor:
    def __init__(self, airdrop_db, airdrop_id, window_id, snapshpt_guid):
        self._airdrop_db = airdrop_db
        self._airdrop_id = airdrop_id
        self._window_id = window_id
        self._snapshot_guid = snapshpt_guid
        self._all_users = []
        self._users_to_reward = []
        self.__insert_reward = "insert into user_rewards (airdrop_id, airdrop_window_id, address, rewards_awarded, score, normalized_score, row_created, row_updated) "+\
                               "values(%s,%s,%s,%s,%s,%s, current_timestamp, current_timestamp) "+\
                               "on duplicate key update rewards_awarded = %s, score = %s, normalized_score = %s, row_updated = current_timestamp"
        self.__insert_audit = "insert into user_rewards_audit (airdrop_id, airdrop_window_id, snapshot_guid, address, balance, staked, score, normalized_score,  "+\
                              "rewards_awarded, comment, row_created, row_updated) "+\
                              "values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, current_timestamp, current_timestamp)"
        self.__reward_rows = []
        self.__reward_audit_rows = []
        self._distinct_snapshots = self.__get_distinct_snapshots()
        return        

    def __get_distinct_snapshots(self):
        result = self._airdrop_db.execute("select count(distinct snapshot_guid) as distinct_snapshots from user_balance_snapshot where airdrop_window_id = %s", [self._window_id])
        return result[0]["distinct_snapshots"]
    
    def __reset_user_rewards(self):
        result = self._airdrop_db.execute("update user_rewards set rewards_awarded = 0, score = 0, normalized_score = 0, row_updated = current_timestamp where airdrop_window_id = %s", [self._window_id])
        return result

    def __get_reward_values(self, user):
        return [self._airdrop_id, self._window_id, getattr(user, "_address"), getattr(user, "_reward"), getattr(user, "_score"), getattr(user, "_log10_score"), 
                getattr(user, "_reward"), getattr(user, "_score"), getattr(user, "_log10_score")]

    def __get_audit_values(self, user):
        return [self._airdrop_id, self._window_id, self._snapshot_guid, getattr(user, "_address"), getattr(user, "_balance"), getattr(user, "_staked"), 
                getattr(user, "_score"), getattr(user, "_log10_score"), getattr(user, "_reward"), getattr(user, "_comment")]

    def __batch_insert(self, values, is_audit_row, force=False):
        query = self.__insert_reward
        rows = self.__reward_rows
        if is_audit_row:
            query = self.__insert_audit
            rows = self.__reward_audit_rows

        number_of_rows = len(rows)
        if (force and number_of_rows > 0) or number_of_rows >= 50:
            self._airdrop_db.bulk_query(query, rows)
            rows.clear()       
        
        if(len(values) > 0):
            rows.append(tuple(values))    

    @exception_handler(SLACK_HOOK=SLACK_HOOK, logger=logger)
    def process_rewards(self):
        rewards_query = "select address, min(total) as balance, min(staked) as staked, count(*) as occurrences " +\
                        "from user_balance_snapshot " +\
                        f"where airdrop_window_id = {self._window_id} and total >= {AGIX_THRESHOLD_IN_COGS} " +\
                        "group by address "
        
        sum_of_log_values = 0
        user_balances = self._airdrop_db.execute(rewards_query)
        for user_balance in user_balances:
            u = UserRewardObject(user_balance["address"], user_balance["balance"], user_balance["staked"])
            self._all_users.append(u)
            if user_balance["occurrences"] < self._distinct_snapshots:
                u.set_comment(f"User appeared only in {user_balance['occurrences']} out of {self._distinct_snapshots} snapshots and hence ignored")
            else:
                self._users_to_reward.append(u)
                sum_of_log_values += getattr(u,"_log10_score")
        
        logger.info(f"Normalized Score {sum_of_log_values} for {len(self._users_to_reward)}")
        try:
            self._airdrop_db.begin_transaction()
            self.__reset_user_rewards()

            for user in self._users_to_reward:
                reward = Decimal(round(getattr(user, "_log10_score") / sum_of_log_values * TOKENS_ALLOCATED_PER_WINDOW, 6) * NUNET_DECIMALS)
                user.set_reward(reward)
                #logger.info(f"Reward for {getattr(user,'_address')} is {reward} {getattr(user, '_score')} {getattr(user, '_log10_score')} ")
                self.__batch_insert(self.__get_reward_values(user), False)

            for user in self._all_users:
                self.__batch_insert(self.__get_audit_values(user), True)
            
            self.__batch_insert([], False, True)
            self.__batch_insert([], True, True)
            self._airdrop_db.commit_transaction()
        except Exception as e:
            logger.error(e)
            self._airdrop_db.rollback_transaction()
            raise(e)
