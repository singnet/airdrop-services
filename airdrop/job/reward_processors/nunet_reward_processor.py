
import time
import math

from decimal import Decimal
from common.exception_handler import exception_handler
from airdrop.config import SLACK_HOOK
from common.logger import get_logger

logger = get_logger(__name__)

TOKENS_ALLOCATED_PER_WINDOW = Decimal(12500000)
SCORE_DENOMINATOR = Decimal(100000)
AGIX_THRESHOLD_IN_COGS = 250000000000

class UserRewardObject:
    def __init__(self, address, balance, staked):
        self._address = address
        self._balance = Decimal(balance)
        self._staked = Decimal(staked)
        self._score = (self._balance + (Decimal(0.2) * self._staked)) / SCORE_DENOMINATOR
        self._log10_score = Decimal(math.log10(self._score + 1))
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
        self.__insert_reward = "insert into user_rewards (airdrop_id, airdrop_window_id, address, rewards_awarded, score, row_created, row_updated) "+\
                          "values(%s,%s,%s,%s,%s, current_timestamp, current_timestamp) "+\
                          "on duplicate key update rewards_awarded = %s, score = %s, row_updated = current_timestamp"
        self.__insert_audit = "insert into user_rewards_audit (airdrop_id, airdrop_window_id, snapshot_guid, address, balance, staked, score, normalized_score, rewards_awarded, message, row_created, row_updated) "+\
                          "values(%s,%s,%s,%s,%s, current_timestamp, current_timestamp) "+\
                          "on duplicate key update rewards_awarded = %s, score = %s, row_updated = current_timestamp"
        self.__rows_to_insert = []
        self._distinct_snapshots = self.__get_distinct_snapshots()
        return        

    def __get_distinct_snapshots(self):
        result = self._airdrop_db.execute("select count(distinct snapshot_guid) as distinct_snapshots from user_balance_snapshot where airdrop_window_id = %s", [self._window_id])
        return result[0]["distinct_snapshots"]

    def __batch_insert(self, values, force=False):
        start = time.process_time()
        number_of_rows = len(self.__rows_to_insert)
        if (force and number_of_rows > 0) or number_of_rows >= 50:
            self._airdrop_db.bulk_query(self.__insert_reward, self.__rows_to_insert)
            self.__rows_to_insert.clear()       
            print(f"*****{(time.process_time() - start)} seconds. Inserted {number_of_rows} rows")
        
        if(len(values) > 0):
            self.__rows_to_insert.append(tuple(values))    

    @exception_handler(SLACK_HOOK=SLACK_HOOK, logger=logger)
    def process_rewards(self):
        rewards_query = "select address, min(balance) as balance, min(staked) as staked, count(*) as occurrences " +\
                        "from user_balance_snapshot " +\
                        f"where airdrop_window_id = 1 and total >= {AGIX_THRESHOLD_IN_COGS} " +\
                        "group by address "
        
        print("********** " + rewards_query)
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
        
        for user in self._users_to_reward:
            reward = getattr(user, "_log10_score") / sum_of_log_values * TOKENS_ALLOCATED_PER_WINDOW
            user.set_reward(reward)
            print(f"Reward for {getattr(user,'_address')} is {reward}")

        

