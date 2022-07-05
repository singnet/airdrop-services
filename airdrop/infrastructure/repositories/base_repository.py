from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from airdrop.config import NETWORK

driver=NETWORK['db']['DB_DRIVER']
host=NETWORK['db']['DB_HOST']
user=NETWORK['db']["DB_USER"]
db_name=NETWORK['db']["DB_NAME"]
password=NETWORK['db']["DB_PASSWORD"]
port=NETWORK['db']["DB_PORT"]

connection_string = f"{driver}://{user}:{password}@{host}:{port}/{db_name}"
engine = create_engine(connection_string, pool_pre_ping=True, echo=False)

Session = sessionmaker(bind=engine)
default_session = Session()


class BaseRepository:
    def __init__(self):
        self.session = default_session

    def add(self, item):
        try:
            self.session.add(item)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def add_all_items(self, items):
        try:
            self.session.add_all(items)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
