from datetime import datetime as dt
from datetime import timedelta


class AirdropData:
    token_address = "0x5e94577b949a56279637ff74dfcff2c28408f049"
    org_name = "Test Organization"
    token_name = "AGIX"
    token_type = "CONTRACT"
    contract_address = "0x5e94577b949a56279637ff74dfcff2c28408f049"
    portal_link = "http://localhost/"
    documentation_link = "http://testlink.test"
    description = "Test description."
    github_link = "https://github.com/test-repository"


class AirdropWindowData:
    airdrop_window_name = "Test Airdrop Window"
    description = 'Test Airdrop'
    registration_required = True
    registration_start_date = dt.utcnow() - timedelta(days=2)
    registration_end_date = dt.utcnow() + timedelta(days=30)
    snapshot_required = True
    claim_start_date = dt.utcnow() - timedelta(days=2)
    claim_end_date = dt.utcnow() + timedelta(days=30)
    total_airdrop_tokens = 1000000
