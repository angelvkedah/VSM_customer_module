from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

import pandas as pd

from utils.helpers import safe_str


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
PRIORITY_RULES_FILE = ASSETS_DIR / "message_priority_rules.csv"


IGNORE_PATTERNS = [
    r"\bпесок\b",
    r"\bпеска\b",
    r"\bзвуков",
    r"\bАЛСН\b",
    r"\bСАУТ\b",
    r"\bБЛОК\b",
]


def contains_ignored_keywords(text: str) -> bool:
    text = safe_str(text)

    if not text:
        return False

    for pattern in IGNORE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True

    return False


@lru_cache(maxsize=1)
def load_priority_rules():
    if not PRIORITY_RULES_FILE.exists():
        raise FileNotFoundError(
            f"Файл не найден: {PRIORITY_RULES_FILE}"
        )

    df = pd.read_csv(PRIORITY_RULES_FILE, encoding="utf-8-sig")

    
    if "meldecode" not in df.columns and "messagecode" in df.columns:
        df = df.rename(columns={"messagecode": "meldecode"})

    required_columns = {
        "meldecode",
        "priority",
        "meldeklasse",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            "В CSV отсутствуют обязательные колонки: "
            + ", ".join(sorted(missing))
        )

    df = df.copy()
    df["meldecode"] = df["meldecode"].apply(safe_str)
    df["priority"] = df["priority"].apply(lambda x: safe_str(x).lower())
    df["meldeklasse"] = df["meldeklasse"].apply(lambda x: safe_str(x).upper())

    return df


@lru_cache(maxsize=1)
def load_priority_rules_by_code():
    df = load_priority_rules()

    mapping = {}

    for _, row in df.iterrows():
        code = safe_str(row.get("meldecode"))

        if not code:
            continue

        mapping[code] = {
            "priority": safe_str(row.get("priority")).lower(),
            "meldeklasse": safe_str(row.get("meldeklasse")).upper(),
        }

    return mapping


def get_priority_by_code(messagecode):
    code = safe_str(messagecode)
    rules = load_priority_rules_by_code()

    if code in rules:
        return rules[code]

    return {
        "priority": "green",
        "meldeklasse": "C",
    }


def classify_message(row):
    messagecode = row.get("messagecode")
    message_text = safe_str(row.get("message_text"))

    rule = get_priority_by_code(messagecode)

    priority = rule["priority"]
    meldeklasse = rule["meldeklasse"]

    ignored = contains_ignored_keywords(message_text)

    if ignored:
        priority = "ignore"

    return pd.Series({
        "priority": priority,
        "meldeklasse": meldeklasse,
        "is_ignored": ignored,
    })


def add_priority_columns(timeline_df):
    if timeline_df is None or timeline_df.empty:
        return timeline_df

    df = timeline_df.copy()

    classified_rows = df.apply(
        classify_message,
        axis=1
    )

    df["priority"] = classified_rows["priority"]
    df["meldeklasse"] = classified_rows["meldeklasse"]
    df["is_ignored"] = classified_rows["is_ignored"]

    return df


def filter_messages_for_llm(timeline_df):
    df = add_priority_columns(timeline_df)

    if df is None or df.empty:
        return df

    filtered_df = df[
        df["priority"].isin(["red", "yellow"])
    ].copy()

    filtered_df = filtered_df.sort_values("timestamp")

    return filtered_df.reset_index(drop=True)