import pandas as pd

from utils.connection_manager import DatabaseConnectionManager


def get_trains_list():
    """
    Возвращает список поездов
    """

    query = """
        SELECT
            train_name,
            train_desc
        FROM trains
        ORDER BY train_desc
    """

    return DatabaseConnectionManager.execute_query(query)


def get_events(
    train_id,
    dt_from,
    dt_to,
    limit=100000
):
    """
    Загружает диагностические сообщения
    """

    query = """
        SELECT
            occts AS timestamp,
            gonets AS gonets,
            messagecode,
            messagestate,
            objectid AS train_id,
            carnumber,
            parsingtime
        FROM events
        WHERE objectid = %(train_id)s
            AND occts >= %(dt_from)s
            AND occts <= %(dt_to)s
        ORDER BY occts
        LIMIT %(limit)s
    """

    params = {
        "train_id": train_id,
        "dt_from": dt_from,
        "dt_to": dt_to,
        "limit": limit,
    }

    df = DatabaseConnectionManager.execute_query(
        query=query,
        params=params
    )

    if df.empty:
        return df

    datetime_columns = [
        "timestamp",
        "gonets",
        "parsingtime",
    ]

    for col in datetime_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                errors="coerce"
            )

    return df