
import sys
sys.path.append('/opt')
import time

from airdrop.cron.repository import Repository
from common.exception_handler import exception_handler
from common.utils import generate_lambda_response
from airdrop.config import BALANCE_DB_CONFIG, NETWORK, SLACK_HOOK
from common.logger import get_logger

logger = get_logger(__name__)

class EligibilityProcessor:
    def __init__(self):
        self._airdrop_db = Repository(NETWORK["db"])
        self._balances_db = Repository(BALANCE_DB_CONFIG)
        self._active_airdrop_windows = []
        self._snapshot_index = 1
        self.__insert_query = "insert into user_balance_snapshot (airdrop_window_id, address, balance, staked, snapshot_index, row_created, row_updated) "+\
                          "values(%s,%s,%s,%s,%s, current_timestamp, current_timestamp)"
        self.__rows_to_insert = []
        return

    def __populate_state(self):
        all_windows = self._airdrop_db.execute("select aw.airdrop_id, aw.row_id as airdrop_window_id from airdrop_window aw, airdrop ad " + \
                                               "where aw.airdrop_id = ad.row_id and ad.check_eligibility = 1 " + \
                                               "and aw.registration_start_period >= current_timestamp order by aw.airdrop_id, aw.registration_start_period asc")
        seen_airdrop_id = -1
        for window in all_windows:
            if seen_airdrop_id == window["airdrop_id"]:
                continue
            self._active_airdrop_windows.append(window["airdrop_window_id"])
            seen_airdrop_id = window["airdrop_id"]
        response = self._airdrop_db.execute("select max(snapshot_index) as snapshot_index from user_balance_snapshot")
        
        print(f"{response} {len(response)} {response[0]} {response[0]['snapshot_index']}")
        if len(response) > 0 and response[0]['snapshot_index'] is not None:
            self._snapshot_index = response[0]['snapshot_index'] + 1
        logger.info(f"Processing eligibility for {len(self._active_airdrop_windows)} windows in snapshot {self._snapshot_index}")

    def __batch_insert(self, values, force=False):
        start = time.process_time()
        number_of_rows = len(self.__rows_to_insert)
        if (force and number_of_rows > 0) or number_of_rows >= 50:
            self._airdrop_db.bulk_query(self.__insert_query, self.__rows_to_insert)
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
            for window in self._active_airdrop_windows:
                self.__batch_insert([window, row["wallet_address"], row["balance"], row["staked"], self._snapshot_index])
        self.__batch_insert([], True)

    def process_eligibility(self):
        self.__populate_state()
        self.__populate_snapshot()



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