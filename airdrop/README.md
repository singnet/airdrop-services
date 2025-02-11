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
sls offline start -s <stage>
```

## Requirements

| Language     | Download                          |
| ------------ | --------------------------------- |
| Python 3.12   | https://www.python.org/downloads/ |
| Node JS 22.13 | https://nodejs.org/en/            |
