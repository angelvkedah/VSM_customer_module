import pandas as pd

from modules.vsm_protocol.vsm_load_data import load_events_data
from modules.vsm_protocol.handlers.decoder import decode_events_df
from modules.vsm_protocol.llm.message_filter import add_priority_columns


def load_analytics_data(
    train_id,
    train_human_name,
    dt_from,
    dt_to,
    limit=500000
):
    """
    Загружает и подготавливает данные для аналитики
    """
    events_df = load_events_data(
        train_id=train_id,
        dt_from=dt_from,
        dt_to=dt_to,
        limit=limit,
    )

    if events_df is None or events_df.empty:
        return pd.DataFrame()

    events_df = decode_events_df(events_df)
    events_df["train_id"] = train_human_name
    events_df["train_name_human"] = train_human_name

    # Добавляем колонки с приоритетами для аналитики
    events_df = add_priority_columns(events_df)

    # Добавляем временные колонки для агрегации
    events_df["hour"] = pd.to_datetime(events_df["timestamp"]).dt.hour
    events_df["day"] = pd.to_datetime(events_df["timestamp"]).dt.date
    events_df["day_of_week"] = pd.to_datetime(events_df["timestamp"]).dt.dayofweek

    return events_df


def load_analytics_data_for_filters(sidebar_data):
    """
    Загружает данные для одного или двух поездов
    """
    all_events = []

    events_df_1 = load_analytics_data(
        train_id=sidebar_data.train_id,
        train_human_name=sidebar_data.train_human_name,
        dt_from=sidebar_data.dt_from,
        dt_to=sidebar_data.dt_to,
    )

    if not events_df_1.empty:
        all_events.append(events_df_1)

    if sidebar_data.mode == "Два поезда" and sidebar_data.train_id_2:
        events_df_2 = load_analytics_data(
            train_id=sidebar_data.train_id_2,
            train_human_name=sidebar_data.train_human_name_2,
            dt_from=sidebar_data.dt_from,
            dt_to=sidebar_data.dt_to,
        )

        if not events_df_2.empty:
            all_events.append(events_df_2)

    if all_events:
        events_df = pd.concat(all_events, ignore_index=True)
    else:
        events_df = pd.DataFrame()

    return events_df