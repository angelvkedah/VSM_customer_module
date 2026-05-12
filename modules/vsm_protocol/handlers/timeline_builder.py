from collections import deque

import pandas as pd

from modules.vsm_protocol.handlers.human_readable import get_human_message_templates


def get_message_text_for_row(row):
    code = row.get("messagecode")
    event_type = row.get("event_type", "activation")

    templates = get_human_message_templates(code)

    if event_type == "activation":
        return templates.get("kurztext_3", "")
    if event_type == "deactivation":
        return templates.get("kurztext_4", "")
    if event_type == "still_active_marker":
        return templates.get("kurztext_3", "")

    return templates.get("kurztext_2", "")


def build_timeline(events_df):
    """
    активация и деактивация отображаются отдельными строками.
    """
    if events_df is None or events_df.empty:
        return pd.DataFrame()

    df = events_df.copy()

    # Приводим названия колонок к ожидаемому виду
    if "occts" in df.columns and "timestamp" not in df.columns:
        df["timestamp"] = df["occts"]

    if "objectid" in df.columns and "train_id" not in df.columns:
        df["train_id"] = df["objectid"]

    df = df.sort_values(
        ["timestamp", "messagestate"],
        ascending=[True, False]
    )

    timeline = []
    active_queues = {}
    next_pair_id = 1
    orphan_deactivations = []

    for _, row in df.iterrows():
        key = (
            row.get("messagecode"),
            row.get("train_id"),
            row.get("carnumber"),
        )

        if key not in active_queues:
            active_queues[key] = deque()

        if row.get("messagestate") is True:
            pair_id = f"pair_{next_pair_id}"
            next_pair_id += 1

            active_event = {
                "train_id": row.get("train_id"),
                "carnumber": row.get("carnumber"),
                "messagecode": row.get("messagecode"),
                "activation_time": row.get("timestamp"),
                "parsingtime": row.get("parsingtime"),
                "pair_id": pair_id,
            }

            active_queues[key].append(active_event)

            timeline.append({
                "train_id": row.get("train_id"),
                "carnumber": row.get("carnumber"),
                "messagecode": row.get("messagecode"),
                "timestamp": row.get("timestamp"),
                "event_type": "activation",
                "pair_id": pair_id,
                "parsingtime": row.get("parsingtime"),
                "activation_time": row.get("timestamp"),
                "deactivation_time": None,
            })

        elif row.get("messagestate") is False:
            if active_queues[key]:
                active_event = active_queues[key].popleft()
                pair_id = active_event["pair_id"]

                deactivation_time = row.get("gonets")
                if deactivation_time is None or pd.isna(deactivation_time):
                    deactivation_time = row.get("timestamp")

                timeline.append({
                    "train_id": row.get("train_id"),
                    "carnumber": row.get("carnumber"),
                    "messagecode": row.get("messagecode"),
                    "timestamp": deactivation_time,
                    "event_type": "deactivation",
                    "pair_id": pair_id,
                    "parsingtime": row.get("parsingtime"),
                    "activation_time": active_event["activation_time"],
                    "deactivation_time": deactivation_time,
                })

            else:
                orphan_pair_id = f"orphan_{next_pair_id}"
                next_pair_id += 1

                orphan_deactivations.append({
                    "train_id": row.get("train_id"),
                    "carnumber": row.get("carnumber"),
                    "messagecode": row.get("messagecode"),
                    "timestamp": row.get("gonets", row.get("timestamp")),
                    "parsingtime": row.get("parsingtime"),
                    "pair_id": orphan_pair_id,
                    "event_type": "deactivation",
                })

    for orphan in orphan_deactivations:
        timeline.append({
            "train_id": orphan["train_id"],
            "carnumber": orphan["carnumber"],
            "messagecode": orphan["messagecode"],
            "timestamp": orphan["timestamp"],
            "event_type": "deactivation",
            "pair_id": orphan["pair_id"],
            "parsingtime": orphan["parsingtime"],
            "activation_time": None,
            "deactivation_time": orphan["timestamp"],
        })

    for _, queue in active_queues.items():
        for active_event in queue:
            timeline.append({
                "train_id": active_event["train_id"],
                "carnumber": active_event["carnumber"],
                "messagecode": active_event["messagecode"],
                "timestamp": active_event["activation_time"],
                "event_type": "still_active_marker",
                "pair_id": active_event["pair_id"],
                "parsingtime": active_event["parsingtime"],
                "activation_time": active_event["activation_time"],
                "deactivation_time": None,
            })

    result_df = pd.DataFrame(timeline)

    if result_df.empty:
        return result_df

    result_df = result_df.sort_values("timestamp").reset_index(drop=True)

    result_df["message_text"] = result_df.apply(
        get_message_text_for_row,
        axis=1
    )

    return result_df