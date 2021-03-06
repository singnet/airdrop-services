import pymysql
from common.logger import get_logger

logger = get_logger(__name__)

class Repository:
    connection = None

    def __init__(self, db):
        self.DB_HOST = db['DB_HOST']
        self.DB_USER = db['DB_USER']
        self.DB_PASSWORD = db['DB_PASSWORD']
        self.DB_NAME = db['DB_NAME']
        self.DB_PORT = db['DB_PORT']
        self.connection = self.__get_connection()
        self.auto_commit = True

    def execute(self, query, params=None):
        return self.__execute_query(query, params)

    def __get_connection(self):
        open = True
        if self.connection is not None:
            try:
                self.execute("select 1")
                open = False
            except Exception as e:
                open = True

        if open:
            self.connection = pymysql.connect(host=self.DB_HOST, user=self.DB_USER, passwd=self.DB_PASSWORD, db=self.DB_NAME, port=self.DB_PORT)
        return self.connection

    def __execute_query(self, query, params=None):
        result = list()
        try:
            with self.connection.cursor() as cursor:
                qry_resp = cursor.execute(query, params)
                db_rows = cursor.fetchall()
                if cursor.description is not None:
                    field_name = [field[0] for field in cursor.description]
                    for values in db_rows:
                        row = dict(zip(field_name, values))
                        result.append(row)
                else:
                    result.append(qry_resp)
                    result.append({'last_row_id': cursor.lastrowid})
                if self.auto_commit:
                    self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"DB Error in {str(query)}, error: {repr(e)}")
            raise e
        return result

    def bulk_query(self, query, params=None):
        try:
            with self.connection.cursor() as cursor:
                result = cursor.executemany(query, params)
                if self.auto_commit:
                    self.connection.commit()
                return result
        except Exception as err:
            if self.auto_commit:
                self.connection.rollback()
            logger.error(f"DB Error in {str(query)}, error: {repr(err)}")

    def begin_transaction(self):
        self.connection.begin()
        self.auto_commit = False

    def commit_transaction(self):
        self.connection.commit()
        self.auto_commit = True

    def rollback_transaction(self):
        self.connection.rollback()