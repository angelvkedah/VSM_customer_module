from modules.vsm_protocol.db.queries import (
    get_trains_list,
    get_events
)


def load_trains_data():
    """
    Загружает и подготавливает список поездов
    """

    trains_df = get_trains_list()

    human_to_train_id = {}
    train_id_to_human = {}

    for _, row in trains_df.iterrows():
        train_name = row["train_name"]
        train_desc = row["train_desc"]

        human_to_train_id[train_desc] = train_name
        train_id_to_human[train_name] = train_desc

    return {
        "trains_df": trains_df,
        "human_to_train_id": human_to_train_id,
        "train_id_to_human": train_id_to_human,
    }


def load_events_data(
    train_id,
    dt_from,
    dt_to,
    limit=100000
):
    """
    Загружает события по поезду
    """

    return get_events(
        train_id=train_id,
        dt_from=dt_from,
        dt_to=dt_to,
        limit=limit
    )