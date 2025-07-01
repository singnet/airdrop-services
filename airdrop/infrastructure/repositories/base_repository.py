from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from airdrop.config import NETWORK


url = URL.create(
    drivername=NETWORK['db']['DB_DRIVER'],
    username=NETWORK['db']["DB_USER"],
    password=NETWORK['db']["DB_PASSWORD"],
    host=NETWORK['db']['DB_HOST'],
    port=NETWORK['db']["DB_PORT"],
    database=NETWORK['db']["DB_NAME"]
)
engine = create_engine(url, pool_pre_ping=True, echo=False, isolation_level="READ COMMITTED")

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
