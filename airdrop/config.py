NETWORK = {
    "name": "test",
    "http_provider": "https://ropsten.infura.io",
    "ws_provider": "wss://ropsten.infura.io/ws",
    "db": {
        "DB_DRIVER": "mysql+pymysql",
        "DB_HOST": "",
        "DB_USER": "",
        "DB_PASSWORD": "",
        "DB_NAME": "",
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


class AirdropStrategy:
    AGIX = "AGIX"
