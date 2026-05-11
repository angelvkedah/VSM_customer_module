from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
HUMAN_MESSAGES_FILE = ASSETS_DIR / "massages_for_protocol.csv"


def _safe_str(value: Any) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


@lru_cache(maxsize=1)
def load_human_messages_dict() -> dict[str, dict[str, str]]:
    if not HUMAN_MESSAGES_FILE.exists():
        raise FileNotFoundError(
            f"Файл справочника не найден: {HUMAN_MESSAGES_FILE}"
        )

    df = pd.read_csv(HUMAN_MESSAGES_FILE, encoding="utf-8-sig")

    required_columns = {
        "meldecode",
        "kurztext_2",
        "kurztext_3",
        "kurztext_4",
    }

    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(
            "В CSV отсутствуют обязательные столбцы: "
            + ", ".join(sorted(missing_columns))
        )

    mapping = {}

    for _, row in df.iterrows():
        code = _safe_str(row.get("meldecode"))
        if not code:
            continue

        mapping[code] = {
            "kurztext_2": _safe_str(row.get("kurztext_2")),
            "kurztext_3": _safe_str(row.get("kurztext_3")),
            "kurztext_4": _safe_str(row.get("kurztext_4")),
        }

    return mapping


def get_human_message_templates(message_code: Any) -> dict[str, str]:
    code = _safe_str(message_code)
    mapping = load_human_messages_dict()

    if code in mapping:
        return mapping[code]

    return {
        "kurztext_2": f"Сообщение с кодом ДС {code}",
        "kurztext_3": f"Поступило ДС {code}",
        "kurztext_4": f"Более не активно ДС {code}",
    }