import json
import sys

from airdrop.job.reward_processors.loyalty_reward_processor import LoyaltyEligibilityProcessor

sys.path.append('/opt')

import time
import uuid

from airdrop.constants import PROCESSOR_PATH
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
        # self._airdrop_windows_open_for_snapshot = []
        self._active_airdrop_window_map = {}
        self._reward_airdrop_window_map = {}
        self._snapshot_guid = str(uuid.uuid4())
        self.__insert_snapshot = "insert into user_balance_snapshot (airdrop_window_id, address, balance, staked, total, snapshot_guid, row_created, row_updated) " + \
                                 "values(%s,%s,%s,%s,%s, %s, current_timestamp, current_timestamp)"
        self.__rows_to_insert = []
        return

    def __populate_state(self):
        all_windows = self._airdrop_db.execute(
            "select aw.airdrop_id, ad.airdrop_processor, aw.row_id as airdrop_window_id from airdrop_window aw, airdrop ad " + \
            "where aw.airdrop_id = ad.row_id and ad.airdrop_processor is not null " + \
            "and current_timestamp between aw.first_snapshot_at and aw.last_snapshot_at ")
        for window in all_windows:
            details = {}
            details["airdrop_id"] = window["airdrop_id"]
            details["airdrop_processor"] = window["airdrop_processor"]
            self._active_airdrop_window_map[window["airdrop_window_id"]] = details
        logger.info("Active windows " + str(self._active_airdrop_window_map))

        reward_windows = self._airdrop_db.execute(
            "select aw.airdrop_id, ad.airdrop_processor, aw.row_id as airdrop_window_id from airdrop_window aw, airdrop ad  " + \
            "where aw.airdrop_id = ad.row_id and ad.airdrop_processor is not null  " + \
            "and current_timestamp between aw.registration_end_period and aw.claim_start_period")
        for window in reward_windows:
            details = {}
            details["airdrop_id"] = window["airdrop_id"]
            details["airdrop_processor"] = window["airdrop_processor"]
            self._reward_airdrop_window_map[window["airdrop_window_id"]] = details
        logger.info("Reward windows " + str(self._reward_airdrop_window_map))

    def __batch_insert(self, values, force=False):
        start = time.process_time()
        number_of_rows = len(self.__rows_to_insert)
        if (force and number_of_rows > 0) or number_of_rows >= 50:
            self._airdrop_db.bulk_query(self.__insert_snapshot, self.__rows_to_insert)
            self.__rows_to_insert.clear()

        if (len(values) > 0):
            self.__rows_to_insert.append(tuple(values))

    def __populate_snapshot(self):
        snapshot_rows = {}
        query = "select wallet_address, sum(amount) as balance from agix_balances " + \
                "where balance_type <> 'STAKED' group by wallet_address having sum(amount) > 0"
        user_balance = self._balances_db.execute(query)
        logger.info(f"Users with balance size is {len(user_balance)} holders")
        for row in user_balance:
            row["staked"] = 0
            row["total"] = row["balance"]
            snapshot_rows[row["wallet_address"]] = row

        logger.info(f"Users with non zero balance size is {len(snapshot_rows)} holders")
        query = "select wallet_address, amount as staked from agix_balances where balance_type = 'STAKED' "
        user_stake = self._balances_db.execute(query)
        logger.info(f"Users with stake size is {len(user_stake)} holders")
        for row in user_stake:
            if row["wallet_address"] in snapshot_rows:
                seen_row = snapshot_rows[row["wallet_address"]]
                seen_row["staked"] = row["staked"]
                seen_row["total"] = Decimal(seen_row["balance"]) + Decimal(seen_row["staked"])
            else:
                row["balance"] = 0
                row["total"] = row["staked"]
                snapshot_rows[row["wallet_address"]] = row

        for address in snapshot_rows:
            for window in self._active_airdrop_window_map:
                self.__batch_insert(
                    [window, address, snapshot_rows[address]["balance"], snapshot_rows[address]["staked"],
                     snapshot_rows[address]["total"], self._snapshot_guid])
        self.__batch_insert([], True)

    def __process_reward(self, processor_name, airdrop_id, window, identifier, only_registered):
        logger.info(
            f"Processing rewards for window {window} using processor {processor_name} with snapshot {identifier}. For all {only_registered}")
        processor_class = locate("airdrop.job.reward_processors." + processor_name)
        processor = processor_class(self._airdrop_db, airdrop_id, window, identifier)
        processor.process_rewards(only_registered)

    def process_specific_reward(self, event):
        self.__process_reward(event['processor_name'], event['airdrop_id'], event['window_id'], "REGISTRATION", False)

    def process_eligibility(self):
        self.__populate_state()

        if len(self._reward_airdrop_window_map) > 0:
            logger.info("Processing final rewards")
            for window in self._reward_airdrop_window_map:
                airdrop_id = self._reward_airdrop_window_map[window]["airdrop_id"]
                airdrop_class_name = self._reward_airdrop_window_map[window]["airdrop_processor"]
                airdrop_class = locate(f"{PROCESSOR_PATH}.{airdrop_class_name}")
                reward_processor_name = airdrop_class(airdrop_id).reward_processor_name
                self.__process_reward(reward_processor_name, airdrop_id, window, "FINAL", True)

        if len(self._active_airdrop_window_map) == 0:
            logger.info(f"No airdrop windows to process for")
            return

        logger.info(
            f"Processing eligibility for windows {self._active_airdrop_window_map.keys()}. Snapshot Index is {self._snapshot_guid}")
        self.__populate_snapshot()
        for window in self._active_airdrop_window_map:
            processor_name = self._active_airdrop_window_map[window]["airdrop_processor"]
            airdrop_id = self._active_airdrop_window_map[window]["airdrop_id"]
            self.__process_reward(processor_name, airdrop_id, window, self._snapshot_guid, False)


@exception_handler(SLACK_HOOK=SLACK_HOOK, logger=logger)
def process_eligibility(event, context):
    logger.info(f"Processing eligibility")

    e = EligibilityProcessor()
    if event is not None and 'window_id' in event:
        e.process_specific_reward(event)
    else:
        e.process_eligibility()

    logger.info(f"Completed Processing eligibility")
    return generate_lambda_response(
        200,
        "Success"
    )


@exception_handler(SLACK_HOOK=SLACK_HOOK, logger=logger)
def process_loyalty_airdrop_reward_eligibility(event, context):
    logger.info(f"Processing loyalty airdrop reward with the event={json.dumps(event)}")

    if not event or not isinstance(event, dict):
        logger.info("Empty event provided for processing or invalid input format provided")
        return generate_lambda_response(
            200,
            "failed"
        )

    airdrop_id = event.get('airdrop_id')
    window_id = event.get('window_id')

    if not airdrop_id or not window_id:
        logger.info(f"Invalid airdrop_id={airdrop_id} or window_id={window_id} provided")
        return generate_lambda_response(
            200,
            "failed"
        )

    response = LoyaltyEligibilityProcessor(airdrop_id=airdrop_id, window_id=window_id).process_reward()

    logger.info(f"Completed Processing eligibility")
    return generate_lambda_response(
        200,
        response
    )
