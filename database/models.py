from sqlalchemy import BIGINT, VARCHAR, Column, TEXT, text, UniqueConstraint, INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import TIMESTAMP, BIT
from sqlalchemy.sql import func


Base = declarative_base()


class AuditClass(object):
    id = Column("row_id", BIGINT, primary_key=True, autoincrement=True)
    row_created = Column(
        "row_created",
        TIMESTAMP(),
        server_default=func.current_timestamp(),
        nullable=False,
    )
    row_updated = Column(
        "row_updated",
        TIMESTAMP(),
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        nullable=False,
    )


class Airdrop(Base):
    __tablename__ = "airdrop"
    id = Column("row_id", INTEGER, primary_key=True, autoincrement=False, unique=True)
    address = Column("address", VARCHAR(50), nullable=False)
    org_name = Column("org_name", VARCHAR(256), nullable=False)
    token_name = Column("token_name", VARCHAR(128), nullable=False)
    token_type = Column("token_type", VARCHAR(50), nullable=False)
    contract_address = Column("contract_address", VARCHAR(50), nullable=False)
    portal_link = Column("portal_link", VARCHAR(256), nullable=True)
    documentation_link = Column("documentation_link", VARCHAR(256), nullable=True)
    description = Column("description", TEXT, nullable=True)
    github_link_for_contract = Column(
        "github_link_for_contract", VARCHAR(256), nullable=True
    )
    row_created = Column(
        "row_created",
        TIMESTAMP(),
        server_default=func.current_timestamp(),
        nullable=False,
    )
    row_updated = Column(
        "row_updated",
        TIMESTAMP(),
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        nullable=False,
    )


class AirdropWindow(Base):
    __tablename__ = "airdrop_window"
    id = Column("row_id", INTEGER, primary_key=True, autoincrement=True)
    airdrop_id = Column("airdrop_id", INTEGER, nullable=False)
    description = Column("description", TEXT, nullable=True)
    registration_required = Column("registration_required", BIT, default=True)
    registration_start_period = Column(
        "registration_start_period", TIMESTAMP(), nullable=False
    )
    registration_end_period = Column(
        "registration_end_period", TIMESTAMP(), nullable=False
    )
    snapshot_required = Column("snapshot_required", BIT, default=True)
    first_snapshot_at = Column("first_snapshot_at", TIMESTAMP(), nullable=True)
    claim_start_period = Column("claim_start_period", TIMESTAMP(), nullable=False)
    claim_end_period = Column("claim_end_period", TIMESTAMP(), nullable=False)
    row_created = Column(
        "row_created",
        TIMESTAMP(),
        server_default=func.current_timestamp(),
        nullable=False,
    )
    row_updated = Column(
        "row_updated",
        TIMESTAMP(),
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        nullable=False,
    )


class AirdropWindowEligibilityRule(Base, AuditClass):
    __tablename__ = "airdropwindow_rules"
    airdrop_window_id = Column("airdrop_window_id", INTEGER, nullable=False)
    rule = Column("rule", TEXT, nullable=False)


class UserBalanceSnapshot(Base, AuditClass):
    __tablename__ = "user_balance_snapshot"
    airdrop_window_id = Column("airdrop_window_id", INTEGER, nullable=False)
    address = Column("address", VARCHAR(50), nullable=False)
    balance = Column("balance", BIGINT, nullable=False)


class UserRegistration(Base, AuditClass):
    __tablename__ = "user_registrations"
    airdrop_window_id = Column("airdrop_window_id", INTEGER, nullable=False)
    address = Column("address", VARCHAR(50), nullable=False, index=True)
    is_eligible = Column("is_eligible", BIT, default=False)
    UniqueConstraint(airdrop_window_id, address, name="uq_airdrop_window_address")


class UserReward(Base, AuditClass):
    __tablename__ = "user_rewards"
    airdrop_window_id = Column("airdrop_window_id", INTEGER, nullable=False)
    address = Column("address", VARCHAR(50), nullable=False, index=True)
    condition = Column("condition", TEXT, nullable=True)
    rewards_awarded = Column("rewards_awarded", INTEGER, nullable=False)


class ClaimHistory(Base, AuditClass):
    __tablename__ = "claim_history"
    airdrop_id = Column("airdrop_id", INTEGER, nullable=False)
    airdrop_window_id = Column("airdrop_window_id", INTEGER, nullable=False)
    address = Column("address", VARCHAR(50), nullable=False, index=True)
    claimable_amount = Column("claimable_amount", INTEGER, nullable=False)
    unclaimed_amount = Column("unclaimed_amount", INTEGER, nullable=False)
    transaction_status = Column("transaction_status", VARCHAR(50), nullable=False)
    transaction_hash = Column("transaction_hash", VARCHAR(256), nullable=True)
