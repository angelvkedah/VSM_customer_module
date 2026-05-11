from pathlib import Path

from modules.vsm_protocol.llm.config import INTRO_PROMPT_PATH
from modules.vsm_protocol.llm.local_model import generate_text
from modules.vsm_protocol.llm.message_filter import filter_messages_for_llm
from modules.vsm_protocol.llm.event_aggregator import (
    build_aggregated_events_text,
    get_aggregation_stats,
)
from utils.helpers import format_datetime


def load_prompt(prompt_path: Path) -> str:
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt-файл не найден: {prompt_path}"
        )

    return prompt_path.read_text(encoding="utf-8")


def build_summary_prompt(
    train_name,
    dt_from,
    dt_to,
    aggregated_summary,
    priority_stats,
):
    template = load_prompt(INTRO_PROMPT_PATH)

    return template.format(
        train_name=train_name,
        dt_from=format_datetime(dt_from),
        dt_to=format_datetime(dt_to),
        aggregated_summary=aggregated_summary,
        priority_stats=priority_stats,
    )


def build_hybrid_protocol_text(
    timeline_df,
    train_name,
    dt_from,
    dt_to,
    max_groups=30,
):
    """
    Формирует интеллектуальное резюме диагностических сообщений.

    Важно:
    - полная хронология сюда больше не вставляется;
    - модель получает только отфильтрованные red/yellow сообщения;
    - шумовые сообщения заранее исключаются.
    """

    filtered_timeline_df = filter_messages_for_llm(timeline_df)

    if filtered_timeline_df is None or filtered_timeline_df.empty:
        return (
            f"В период с {format_datetime(dt_from)} по {format_datetime(dt_to)} "
            f"по электропоезду {train_name} значимых диагностических сообщений "
            "для формирования интеллектуального резюме не выявлено."
        )

    aggregated_summary = build_aggregated_events_text(
        filtered_timeline_df,
        max_groups=max_groups,
    )

    priority_stats = get_aggregation_stats(
        filtered_timeline_df
    )

    prompt = build_summary_prompt(
        train_name=train_name,
        dt_from=dt_from,
        dt_to=dt_to,
        aggregated_summary=aggregated_summary,
        priority_stats=priority_stats,
    )

    summary_text = generate_text(prompt)

    return summary_text.strip()