from contextlib import contextmanager
import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv


load_dotenv()


class DatabaseConnectionManager:
    """
    Менеджер подключений к PostgreSQL
    """

    @staticmethod
    def get_connection_config():
        return {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
        }

    @staticmethod
    @contextmanager
    def get_connection():
        conn = None

        try:
            conn = psycopg2.connect(
                **DatabaseConnectionManager.get_connection_config()
            )

            yield conn

        finally:
            if conn:
                conn.close()

    @staticmethod
    def execute_query(query, params=None):
        with DatabaseConnectionManager.get_connection() as conn:
            if params:
                return pd.read_sql(query, conn, params=params)

            return pd.read_sql(query, conn)