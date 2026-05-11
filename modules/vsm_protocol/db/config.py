import os

from dotenv import load_dotenv


load_dotenv()


class DBConfig:
    """
    Конфигурация подключения к PostgreSQL
    """

    @staticmethod
    def get_config():
        config = {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
        }

        missing_keys = [
            key for key, value in config.items()
            if value is None or value == ""
        ]

        if missing_keys:
            raise ValueError(
                "Не заполнены параметры подключения к БД: "
                + ", ".join(missing_keys)
            )

        return config