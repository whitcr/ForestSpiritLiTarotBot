import logging
import asyncpg
from asyncpg import PostgresError
from contextlib import asynccontextmanager
from config import load_config

config = load_config()
NAME_DB = config.db.database
HOST_DB = config.db.db_host
USER_DB = config.db.db_user
PASSWORD_DB = config.db.db_password


@asynccontextmanager
async def connect():
    try:
        conn = await asyncpg.connect(
            host = HOST_DB,
            user = USER_DB,
            password = PASSWORD_DB,
            database = NAME_DB,
            port = 5432
        )
        try:
            yield conn
        finally:
            await conn.close()
    except PostgresError as e:
        logging.error(f"Database error: {e}")
        raise


async def execute_query(query: str, params: tuple = None):
    try:
        async with connect() as conn:
            async with conn.transaction():
                if params:
                    await conn.execute(query, *params)
                else:
                    await conn.execute(query)
    except PostgresError as e:
        logging.error(f"Executing query execution error: {e}")
        raise


async def execute_select(query: str, params: tuple = None):
    try:
        async with connect() as conn:
            result = await conn.fetchval(query, *params if params else ())
            return result if result is not None else False
    except PostgresError as e:
        logging.error(f"Select query execution error: {e}")
        raise


async def execute_select_all(query: str, params: tuple = None):
    try:
        async with connect() as conn:
            result = await conn.fetch(query, *params if params else ())
            return result if result is not None else False
    except PostgresError as e:
        logging.error(f"Select all query execution error: {e}")
        raise
