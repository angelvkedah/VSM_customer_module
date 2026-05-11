import pandas as pd

from modules.vsm_protocol.handlers.human_readable import get_human_message_templates
from utils.helpers import safe_str


def decode_message(code):
    templates = get_human_message_templates(code)
    return templates.get("kurztext_2") or f"Сообщение с кодом ДС {safe_str(code)}"


def decode_events_df(df):
    if df is not None and not df.empty:
        df = df.copy()
        df["message_text"] = df["messagecode"].apply(decode_message)

    return df