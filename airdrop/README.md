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

1) Create airdrop/config.py file by example airdrop/config.example.py file
2) Start the service:
```sh
sls offline start -s <stage>
```

## Note:
When creating the last database migration to create a revision, I had to remove 'airdrop.' from the airdrop/alembic/env.py file in the lines 'from airdrop.infrastructure.models import Base' and 'from airdrop.config import NETWORK', otherwise it didn't work.

## Requirements

| Language     | Download                          |
| ------------ | --------------------------------- |
| Python 3.12   | https://www.python.org/downloads/ |
| Node JS 22.13 | https://nodejs.org/en/            |
