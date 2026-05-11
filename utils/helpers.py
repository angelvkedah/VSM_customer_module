import re
from datetime import datetime
from typing import Any

import pandas as pd


def safe_str(value: Any) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


def format_datetime(dt: Any) -> str:
    if dt is None:
        return ""

    try:
        if pd.isna(dt):
            return ""
    except Exception:
        pass

    if isinstance(dt, (datetime, pd.Timestamp)):
        try:
            return dt.strftime("%d.%m.%Y %H:%M:%S")
        except Exception:
            return str(dt)

    return str(dt)


def clean_text(text: Any, max_length: int = 500) -> str:
    text = safe_str(text)

    if not text:
        return ""

    text = text.replace("\x00", "")
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    if len(text) > max_length:
        text = text[: max_length - 3] + "..."

    return text


def format_car_number(carnumber: Any) -> str:
    car = safe_str(carnumber)

    if not car:
        return ""

    last_two = car[-2:]

    if last_two.isdigit():
        car_index = int(last_two)

        if car_index > 0:
            return f"+{car_index * 100}"

    return car