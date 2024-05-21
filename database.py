import logging
import psycopg2
from psycopg2 import DatabaseError

from contextlib import contextmanager, closing


@contextmanager
def connect():
    try:
        db = psycopg2.connect(
            host = "ec2-52-211-109-211.eu-west-1.compute.amazonaws.com",
            user = "mqrnhmqfzcolwf",
            password = "23abfe9adc4e4b3ee9354b6ff4683564a31e621422d23d722c757450c60e66bd",
            dbname = "df2olk8dol9q7l",
            port = "5432"
        )
        try:
            yield db
        finally:
            db.close()
    except psycopg2.OperationalError as e:
        logging.error(e)


def execute_query(query: str, params: tuple = None):
    try:
        with connect() as db:
            with closing(db.cursor()) as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
            db.commit()
    except DatabaseError as e:
        logging.error(e)
        try:
            db.rollback()
        except DatabaseError as e:
            logging.error(f"Ошибка при откате транзакции: {e}")


def execute_select(query: str, params: tuple = None):
    try:
        with connect() as db:
            with closing(db.cursor()) as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchone()[0]
    except DatabaseError as e:
        logging.error(e)


def execute_select_all(query: str, params: tuple = None):
    try:
        with connect() as db:
            with closing(db.cursor()) as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
    except DatabaseError as e:
        logging.error(e)
