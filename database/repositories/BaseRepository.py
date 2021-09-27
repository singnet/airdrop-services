from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL
from config.database import DATABASE


connection_string = URL.create(
    drivername=DATABASE["DB_DRIVER"],
    host=DATABASE["DB_HOST"],
    username=DATABASE["DB_USER"],
    database=DATABASE["DB_NAME"],
    password=DATABASE["DB_PASSWORD"],
    port=DATABASE["DB_PORT"],
)

engine = create_engine(
    url=connection_string,
    pool_size=1,
    max_overflow=0,
    pool_recycle=3600,
    pool_pre_ping=True,
    pool_use_lifo=True,
    echo=DATABASE["DB_LOGGING"],
)

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

    def add_all(self, items):
        try:
            self.session.bulk_save_objects(items)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
