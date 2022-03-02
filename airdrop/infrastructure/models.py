from sqlalchemy import (
    BIGINT,
    BigInteger,
    VARCHAR,
    Column,
    DECIMAL,
    TEXT,
    text,
    UniqueConstraint,
    INTEGER,
    ForeignKey,
    JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import TIMESTAMP, BIT
from sqlalchemy.orm.relationships import foreign
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

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


class Airdrop(Base, AuditClass):
    __tablename__ = "airdrop"
    token_address = Column("token_address", VARCHAR(50), nullable=False)
    org_name = Column("org_name", VARCHAR(256), nullable=False)
    token_name = Column("token_name", VARCHAR(128), nullable=False)
    token_type = Column("token_type", VARCHAR(50), nullable=False)
    contract_address = Column("contract_address", VARCHAR(50), nullable=False)
    staking_contract_address = Column(
        "staking_contract_address", VARCHAR(50), nullable=True)
    stakable_token_name = Column(
        "stakable_token_name", VARCHAR(50), nullable=True)
    portal_link = Column("portal_link", VARCHAR(256), nullable=True)
    documentation_link = Column(
        "documentation_link", VARCHAR(256), nullable=True)
    description = Column("description", TEXT, nullable=True)
    github_link_for_contract = Column(
        "github_link_for_contract", VARCHAR(256), nullable=True
    )
    rewards_processor = Column("rewards_processor", VARCHAR(256), default=False)
    airdrop_rules = Column("airdrop_rules", JSON, nullable=True)


class AirdropWindow(Base, AuditClass):
    __tablename__ = "airdrop_window"
    airdrop_id = Column(
        BIGINT, ForeignKey("airdrop.row_id", ondelete="CASCADE"), nullable=False
    )
    airdrop_window_order = Column("airdrop_window_order", INTEGER, default=1)
    airdrop_window_name = Column(
        "airdrop_window_name", VARCHAR(256), nullable=False)
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
    last_snapshot_at = Column("last_snapshot_at", TIMESTAMP(), nullable=True)
    claim_start_period = Column(
        "claim_start_period", TIMESTAMP(), nullable=False)
    claim_end_period = Column("claim_end_period", TIMESTAMP(), nullable=False)
    total_airdrop_tokens = Column("total_airdrop_tokens", INTEGER, default=0)
    airdrop = relationship(Airdrop, backref="windows")


class AirdropWindowEligibilityRule(Base, AuditClass):
    __tablename__ = "airdropwindow_rules"
    airdrop_window_id = Column(
        BIGINT,
        ForeignKey("airdrop_window.row_id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column("title", TEXT, nullable=True)
    rule = Column("rule", TEXT, nullable=False)
    airdrop_window = relationship(
        AirdropWindow, backref="airdropwindow_rules")


class AirdropWindowTimelines(Base, AuditClass):
    __tablename__ = "airdropwindow_timeline"
    airdrop_window_id = Column(
        BIGINT,
        ForeignKey("airdrop_window.row_id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column("title", TEXT, nullable=False)
    description = Column("description", TEXT, nullable=False)
    date = Column("date", TIMESTAMP(), nullable=False)
    airdrop_window = relationship(AirdropWindow, backref="timelines")

class UserBalanceSnapshot(Base, AuditClass):
    __tablename__ = "user_balance_snapshot"
    airdrop_window_id = Column(
        BIGINT,
        ForeignKey("airdrop_window.row_id", ondelete="RESTRICT"),
        nullable=False,
    )
    address = Column("address", VARCHAR(50), nullable=False)
    balance = Column("balance", BIGINT, nullable=False)
    staked = Column("staked", BIGINT, nullable=False)
    total = Column("total", BIGINT, nullable=False)
    snapshot_guid = Column("snapshot_guid", VARCHAR(50), nullable=False)


class UserRegistration(Base, AuditClass):
    __tablename__ = "user_registrations"
    airdrop_window_id = Column(
        BIGINT,
        ForeignKey("airdrop_window.row_id", ondelete="RESTRICT"),
        nullable=False,
    )
    address = Column("address", VARCHAR(50), nullable=False, index=True)
    registered_at = Column("registered_at", TIMESTAMP(), nullable=True)
    reject_reason = Column("reject_reason", JSON, nullable=True)
    receipt_generated = Column("receipt_generated", VARCHAR(250), nullable=True, index=True)
    UniqueConstraint(airdrop_window_id, address)
    airdrop_window = relationship(AirdropWindow, backref="users")


class UserReward(Base, AuditClass):
    __tablename__ = "user_rewards"
    airdrop_id = Column(
        BIGINT,
        ForeignKey("airdrop.row_id", ondelete="RESTRICT"),
        nullable=False,
    )
    airdrop_window_id = Column(
        BIGINT,
        ForeignKey("airdrop_window.row_id", ondelete="RESTRICT"),
        nullable=False,
    )
    address = Column("address", VARCHAR(50), nullable=False, index=True)
    condition = Column("condition", TEXT, nullable=True)
    rewards_awarded = Column("rewards_awarded", VARCHAR(50), nullable=False)
    score = Column("score", DECIMAL(18,8), nullable=False)
    normalized_score = Column("normalized_score", DECIMAL(18,8), nullable=False)
    UniqueConstraint(airdrop_window_id, address)

class UserRewardAudit(Base, AuditClass):
    __tablename__ = "user_rewards_audit"
    airdrop_id = Column(
        BIGINT,
        nullable=False,
    )
    airdrop_window_id = Column(
        BIGINT,
        nullable=False,
    )
    address = Column("address", VARCHAR(50), nullable=False, index=True)
    balance = Column("balance", BIGINT, nullable=False)
    staked = Column("staked", BIGINT, nullable=False)
    score = Column("score", DECIMAL(18,8), nullable=False)
    normalized_score = Column("normalized_score", DECIMAL(18,8), nullable=False)
    rewards_awarded = Column("rewards_awarded", VARCHAR(50), nullable=False)
    snapshot_guid = Column("snapshot_guid", VARCHAR(50), nullable=False)
    comment = Column("comment", VARCHAR(512))

class UserNotifications(Base, AuditClass):
    __tablename__ = "user_notifications"
    email = Column("email", VARCHAR(255), nullable=False)
    #ideally this should have been referenced as a foreign key from airdrop table , however
    # we do not want to be overly strict here and also keep this change backward compatible , hence making this nullable
    airdrop_id = Column("airdrop_id", BIGINT, nullable=True)
    UniqueConstraint(email,airdrop_id)


class ClaimHistory(Base, AuditClass):
    __tablename__ = "claim_history"
    airdrop_id = Column(
        BIGINT,
        ForeignKey("airdrop.row_id", ondelete="RESTRICT"),
        nullable=False,
    )
    airdrop_window_id = Column(
        BIGINT,
        ForeignKey("airdrop_window.row_id", ondelete="RESTRICT"),
        nullable=False,
    )
    address = Column("address", VARCHAR(50), nullable=False, index=True)
    blockchain_method = Column("blockchain_method", VARCHAR(50), nullable=True)
    claimable_amount = Column("claimable_amount", INTEGER, nullable=False)
    unclaimed_amount = Column("unclaimed_amount", INTEGER, nullable=False)
    transaction_status = Column(
        "transaction_status", VARCHAR(50), nullable=False)
    transaction_hash = Column("transaction_hash", VARCHAR(256), nullable=True)
    claimed_on = Column("claimed_on", TIMESTAMP(), nullable=True)
    user_registrations = relationship(
        UserRegistration, backref="claim_history", primaryjoin=airdrop_window_id == foreign(UserRegistration.airdrop_window_id), lazy="joined", uselist=False)
