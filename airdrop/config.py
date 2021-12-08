NETWORK = {
    "name": "test",
    "http_provider": "https://ropsten.infura.io/v3/a1b96bbe33004a9d9039ec41d7a8677c",
    "ws_provider": "wss://ropsten.infura.io/ws/v3/a1b96bbe33004a9d9039ec41d7a8677c",
    "db": {
        "DB_DRIVER": "mysql+pymysql",
        "DB_HOST": "localhost",
        "DB_USER": "admin",
        "DB_PASSWORD": "password",
        "DB_NAME": "airdrop",
        "DB_PORT": 3306,
        "DB_LOGGING": True,
    },
}
NETWORK_ID = 3
SLACK_HOOK = {
    "hostname": "",
    "port": 443,
    "path": "",
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
}

SIGNER_PRIVATE_KEY = 'AIRDROP_SIGNER_PRIVATE_KEY'
SIGNER_PRIVATE_KEY_STORAGE_REGION = ''


class AirdropStrategy:
    AGIX = "AGIX"
