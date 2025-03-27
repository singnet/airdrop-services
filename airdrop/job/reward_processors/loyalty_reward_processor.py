from airdrop.config import NETWORK, TOKEN_SNAPSHOT_DB_CONFIG, TOTAL_LOYALTY_REWARD_IN_COGS, \
    TOTAL_WALLET_BALANCE_IN_COGS, TOTAL_STAKE_BALANCE_IN_COGS, EXCLUDED_LOYALTY_WALLETS
from airdrop.job.repository import Repository
from airdrop.utils import datetime_in_utcnow
from common.logger import get_logger

logger = get_logger(__name__)


class LoyaltyEligibilityProcessor:
    def __init__(self, airdrop_id, window_id):
        self.current_datetime = datetime_in_utcnow()
        self._airdrop_db = Repository(NETWORK["db"])
        self._token_snapshot_db = Repository(TOKEN_SNAPSHOT_DB_CONFIG)
        self._airdrop_id = airdrop_id
        self._window_id = window_id
        excluded_wallets = "('" + "','".join(str(x) for x in EXCLUDED_LOYALTY_WALLETS) + "')"
        self.__eligible_user_query = "SELECT * FROM (SELECT sts.staker_address, tsm.wallet_address ," \
                                     "sts.balance_in_cogs AS staker_balance, tsm.balance_in_cogs AS " \
                                     "wallet_balance, tsm.is_contract  FROM staking_token_snapshots sts LEFT JOIN " \
                                     "token_snapshots_00MINS tsm ON sts.staker_address = tsm.wallet_address UNION " \
                                     "SELECT sts.staker_address, tsm.wallet_address ,sts.balance_in_cogs AS stake_balance ," \
                                     "tsm.balance_in_cogs AS wallet_balance, tsm.is_contract FROM staking_token_snapshots sts RIGHT JOIN " \
                                     "token_snapshots_00MINS tsm  ON sts.staker_address = tsm.wallet_address ) a  where " \
                                     "( wallet_balance >= 1000000000 or staker_balance >= 1000000000 )and (" \
                                     f"wallet_address is null or  wallet_address not in {excluded_wallets}) "
        self.__insert_reward = "insert into user_rewards (airdrop_id, airdrop_window_id, address, rewards_awarded, " \
                               "score, normalized_score, row_created, row_updated) " + \
                               "values(%s,%s,%s,%s,0,0, current_timestamp, current_timestamp)  " + \
                               "on duplicate key update rewards_awarded = %s, score = 0, normalized_score = 0, row_updated = current_timestamp"
        self._window_detail_query = f"select a.org_name , a.token_name , aw.registration_start_period , " \
                                    "aw.registration_end_period , aw.claim_start_period , aw.claim_end_period from airdrop " \
                                    f"a join airdrop_window aw on a.row_id = aw.airdrop_id where a.row_id = {self._airdrop_id} and " \
                                    f"aw.row_id = {self._window_id} "
        self._total_windows_query = f"select count(*) as count from airdrop_window aw where aw.airdrop_id = {self._airdrop_id}"

        self.total_no_of_windows = 0

    def get_eligible_users(self):
        users = self._token_snapshot_db.execute(self.__eligible_user_query)
        return users

    def calculate_reward(self, wallet_balance_in_cogs, stake_balance_in_cogs):

        if not wallet_balance_in_cogs:
            wallet_balance_in_cogs = 0
        if not stake_balance_in_cogs:
            stake_balance_in_cogs = 0

        wallet_proportion = (wallet_balance_in_cogs + stake_balance_in_cogs) / TOTAL_WALLET_BALANCE_IN_COGS
        stake_proportion = stake_balance_in_cogs / TOTAL_STAKE_BALANCE_IN_COGS

        wallet_bonus = wallet_proportion * 0.8 * TOTAL_LOYALTY_REWARD_IN_COGS
        stake_bonus = stake_proportion * 0.2 * TOTAL_LOYALTY_REWARD_IN_COGS

        total_reward = (wallet_bonus + stake_bonus) / self.total_no_of_windows

        return int(total_reward)

    def validate_loyalty_reward(self):
        logger.info("Validating the loyalty reward ")
        validation_flag = True
        window_detail = self._airdrop_db.execute(self._window_detail_query)

        # Validate airdrop id and window id
        if not window_detail or not len(window_detail):
            logger.info(f"Unexpected airdrop_id={self._airdrop_id} or window_id={self._window_id} "
                        f"received for processing")
            validation_flag = False
            return validation_flag

        window_detail = window_detail[0]

        claim_start_date = window_detail.get('claim_start_period')
        registration_start_date = window_detail.get('registration_start_period')

        # Validate reward job based on registration start and claim start time
        if not registration_start_date or not claim_start_date or not self.current_datetime > registration_start_date \
                or not self.current_datetime < claim_start_date:
            logger.info(f"Not allowed to process further because either current datetime={self.current_datetime} is "
                        f"less than registration date={registration_start_date} or greater than claim"
                        f" start date={claim_start_date}")
            validation_flag = False
            return validation_flag

        token_name = window_detail.get("token_name")

        # Validate that loyalty reward processes only AGIX
        if not token_name or token_name != "AGIX":
            logger.info(f"Invalid token name={token_name} provided for processing, as loyalty airdrop will process "
                        f"only for AGIX for now")
            validation_flag = False

        return validation_flag

    def set_total_windows(self):
        logger.info(f"Setting the total no of windows for the given airdrop id = {self._airdrop_id}")
        windows = self._airdrop_db.execute(self._total_windows_query)
        self.total_no_of_windows = windows[0]['count']

    def process_reward(self):
        logger.info(f"Processing the reward for the airdrop_id={self._airdrop_id}, window_id={self._window_id}")

        if not self.validate_loyalty_reward():
            logger.info("Validation failed for loyalty reward processing")
            return "Validation failed"

        self.set_total_windows()
        eligible_users = self.get_eligible_users()
        logger.info(f"Total eligible users={len(eligible_users)}")

        final_users = list()
        for eligible_user in eligible_users:
            address = eligible_user.get('wallet_address')
            if not address:
                address = eligible_user.get('staker_address')

            reward = self.calculate_reward(stake_balance_in_cogs=eligible_user.get('staker_balance'),
                                           wallet_balance_in_cogs=eligible_user.get('wallet_balance'))
            final_users.append(
                tuple([self._airdrop_id, self._window_id, address, reward, reward]))

        if len(final_users):
            self._airdrop_db.bulk_query(self.__insert_reward, final_users)

        return f"{len(final_users)} users are eligible for claim on airdrop_id={self._airdrop_id}, " \
               f"window_id={self._window_id}"
