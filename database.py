import logging
import asyncpg
from asyncpg import PostgresError
from config import load_config


class DatabaseManager:
    _pool = None

    @classmethod
    async def get_pool(cls):
        if cls._pool is None:
            config = load_config()
            cls._pool = await asyncpg.create_pool(
                host = config.db.db_host,
                user = config.db.db_user,
                password = config.db.db_password,
                database = config.db.database,
                port = 5432,
                min_size = 1,
                max_size = 10
            )
        return cls._pool

    @classmethod
    async def execute_query(cls, query: str, params: tuple = None):
        try:
            pool = await cls.get_pool()
            async with pool.acquire() as conn:
                async with conn.transaction():
                    if params:
                        await conn.execute(query, *params)
                    else:
                        await conn.execute(query)
        except PostgresError as e:
            logging.error(f"Executing query execution error: {e}")
            raise

    @classmethod
    async def execute_select(cls, query: str, params: tuple = None):
        try:
            pool = await cls.get_pool()
            async with pool.acquire() as conn:
                result = await conn.fetchval(query, *params if params else ())
                return result if result is not None else False
        except PostgresError as e:
            logging.error(f"Select query execution error: {e}")
            raise

    @classmethod
    async def execute_select_all(cls, query: str, params: tuple = None):
        try:
            pool = await cls.get_pool()
            async with pool.acquire() as conn:
                result = await conn.fetch(query, *params if params else ())
                return result if result is not None else False
        except PostgresError as e:
            logging.error(f"Select all query execution error: {e}")
            raise

    @classmethod
    async def close_pool(cls):
        if cls._pool:
            await cls._pool.close()


execute_query = DatabaseManager.execute_query
execute_select = DatabaseManager.execute_select
execute_select_all = DatabaseManager.execute_select_all
