# Airdrop Services

Backend for the Airdrop services

Install the dependencies and devDependencies and start the service locally.

```sh
npm install -g serverless # Install serverless
npm install --save-dev
```

Configure database from `config.py`

```sh
pip3 install -r requirements.txt
alembic upgrade head # Sync database tables
```

### Start the service

```sh
sls offline start
```

## Requirements

| Language     | Download                          |
| ------------ | --------------------------------- |
| Python 3.8   | https://www.python.org/downloads/ |
| Node JS 12.X | https://nodejs.org/en/            |
