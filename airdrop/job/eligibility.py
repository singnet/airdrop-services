
import sys
sys.path.append('/opt')
import time
import uuid

from airdrop.job.repository import Repository
from common.exception_handler import exception_handler
from common.utils import generate_lambda_response
from airdrop.config import BALANCE_DB_CONFIG, NETWORK, SLACK_HOOK
from common.logger import get_logger
from pydoc import locate
from decimal import Decimal

logger = get_logger(__name__)

class EligibilityProcessor:
    def __init__(self):
        self._airdrop_db = Repository(NETWORK["db"])
        self._balances_db = Repository(BALANCE_DB_CONFIG)
        #self._airdrop_windows_open_for_snapshot = []
        self._active_airdrop_window_map = {}
        self._snapshot_guid = str(uuid.uuid4())
        self.__insert_snapshot = "insert into user_balance_snapshot (airdrop_window_id, address, balance, staked, total, snapshot_guid, row_created, row_updated) "+\
                          "values(%s,%s,%s,%s,%s, %s, current_timestamp, current_timestamp)"
        self.__rows_to_insert = []
        return

    def __populate_state(self):
        all_windows = self._airdrop_db.execute("select aw.airdrop_id, ad.rewards_processor, aw.row_id as airdrop_window_id from airdrop_window aw, airdrop ad " + \
                                               "where aw.airdrop_id = ad.row_id and ad.rewards_processor is not null " + \
                                               "and current_timestamp between aw.first_snapshot_at and aw.last_snapshot_at ")
        for window in all_windows:
            details = {}
            details["airdrop_id"] = window["airdrop_id"]
            details["rewards_processor"] = window["rewards_processor"]
            self._active_airdrop_window_map[window["airdrop_window_id"]] = details
        
    def __batch_insert(self, values, force=False):
        start = time.process_time()
        number_of_rows = len(self.__rows_to_insert)
        if (force and number_of_rows > 0) or number_of_rows >= 50:
            self._airdrop_db.bulk_query(self.__insert_snapshot, self.__rows_to_insert)
            self.__rows_to_insert.clear()       
            print(f"*****{(time.process_time() - start)} seconds. Inserted {number_of_rows} rows")
        
        if(len(values) > 0):
            self.__rows_to_insert.append(tuple(values))

    def __populate_snapshot(self):
        query = "select aa.wallet_address, aa.balance, ab.staked from " +\
                "(select wallet_address, sum(amount) as balance from agix_balances " +\
                "where balance_type <> 'STAKED' group by wallet_address) as aa, " +\
                "(select wallet_address, amount as staked from agix_balances where balance_type = 'STAKED') as ab " +\
                "where aa.wallet_address = ab.wallet_address"
        snapshot = self._balances_db.execute(query)
        logger.info(f"Snapshot size is {len(snapshot)} holders")

        for row in snapshot:
            for window in self._active_airdrop_window_map:
                total = Decimal(row["balance"]) + Decimal(row["staked"])
                self.__batch_insert([window, row["wallet_address"], row["balance"], row["staked"], total, self._snapshot_guid])
        self.__batch_insert([], True)

    def process_eligibility(self):
        self.__populate_state()
        if len(self._active_airdrop_window_map) == 0:
            logger.info(f"No airdrop windows to process for")
            return
        
        logger.info(f"Processing eligibility for windows {self._active_airdrop_window_map.keys()}. Snapshot Index is {self._snapshot_guid}")
        #self.__populate_snapshot()
        
        for window in self._active_airdrop_window_map:
            processor_name = self._active_airdrop_window_map[window]["rewards_processor"]
            processor_class = locate("airdrop.job.reward_processors."+processor_name)
            processor = processor_class(self._airdrop_db, self._active_airdrop_window_map[window]["airdrop_id"],window, self._snapshot_guid)
            processor.process_rewards()


@exception_handler(SLACK_HOOK=SLACK_HOOK, logger=logger)
def process_eligibility(event, context):      
    logger.info(f"Processing eligibility")

    e = EligibilityProcessor()
    e.process_eligibility()
    
    logger.info(f"Completed Processing eligibility")
    return generate_lambda_response(
        200,
        "Success"
    )


process_eligibility(None, None)