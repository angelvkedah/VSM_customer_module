from __future__ import annotations

import pandas as pd

from utils.helpers import (
    safe_str,
    format_datetime,
    format_car_number,
)


def _priority_rank(priority: str) -> int:
    priority = safe_str(priority).lower()

    if priority == "red":
        return 3

    if priority == "yellow":
        return 2

    if priority == "green":
        return 1

    return 0


def aggregate_events(timeline_df):
    """
    Агрегирует значимые события.
    """

    if timeline_df is None or timeline_df.empty:
        return pd.DataFrame()

    df = timeline_df.copy()

    if "priority" not in df.columns:
        return pd.DataFrame()

    group_columns = [
        "priority",
        "meldeklasse",
        "train_id",
        "carnumber",
        "messagecode",
        "message_text",
    ]

    aggregated_rows = []

    grouped = df.groupby(
        group_columns,
        dropna=False
    )

    for group_values, group_df in grouped:
        (
            priority,
            meldeklasse,
            train_id,
            carnumber,
            messagecode,
            message_text,
        ) = group_values

        timestamps = group_df["timestamp"].dropna()

        if timestamps.empty:
            continue

        aggregated_rows.append({
            "priority": priority,
            "priority_rank": _priority_rank(priority),
            "meldeklasse": meldeklasse,
            "train_id": train_id,
            "carnumber": carnumber,
            "messagecode": messagecode,
            "message_text": message_text,
            "first_time": timestamps.min(),
            "last_time": timestamps.max(),
            "event_count": len(group_df),
        })

    result_df = pd.DataFrame(aggregated_rows)

    if result_df.empty:
        return result_df

    result_df = result_df.sort_values(
        by=[
            "priority_rank",
            "first_time",
        ],
        ascending=[
            False,
            True,
        ]
    )

    return result_df.reset_index(drop=True)


def build_aggregated_events_text(
    timeline_df,
    max_groups=30
):
    """
    Формирует текст событий для подачи в модель.
    """

    aggregated_df = aggregate_events(timeline_df)

    if aggregated_df.empty:
        return (
            "Значимые диагностические события "
            "не обнаружены."
        )

    aggregated_df = aggregated_df.head(max_groups)

    lines = []

    for _, row in aggregated_df.iterrows():
        priority = safe_str(
            row.get("priority")
        ).lower()

        if priority == "red":
            importance = "КРИТИЧЕСКОЕ СООБЩЕНИЕ"
        else:
            importance = "ЗНАЧИМОЕ СООБЩЕНИЕ"

        lines.extend([
            importance,
            (
                f"Код ДС: "
                f"[{safe_str(row.get('messagecode'))}]"
            ),
            (
                f"Поезд: "
                f"{safe_str(row.get('train_id'))}"
            ),
            (
                f"Вагон: "
                f"{format_car_number(row.get('carnumber'))}"
            ),
            (
                f"Описание: "
                f"{safe_str(row.get('message_text'))}"
            ),
            (
                f"Период фиксации: "
                f"с {format_datetime(row.get('first_time'))} "
                f"по {format_datetime(row.get('last_time'))}"
            ),
            "",
        ])

    return "\n".join(lines)


def get_aggregation_stats(timeline_df):
    """
    Возвращает статистику агрегации.
    """

    aggregated_df = aggregate_events(timeline_df)

    if aggregated_df.empty:
        return {
            "red_groups": 0,
            "yellow_groups": 0,
            "total_groups": 0,
        }

    return {
        "red_groups": len(
            aggregated_df[
                aggregated_df["priority"] == "red"
            ]
        ),
        "yellow_groups": len(
            aggregated_df[
                aggregated_df["priority"] == "yellow"
            ]
        ),
        "total_groups": len(aggregated_df),
    }