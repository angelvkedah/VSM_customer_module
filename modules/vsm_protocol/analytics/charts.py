import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_priority_distribution_chart(df):
    """
    Распределение сообщений по приоритетам
    """
    if df.empty or "priority" not in df.columns:
        return None

    priority_counts = df["priority"].value_counts().reset_index()
    priority_counts.columns = ["Приоритет", "Количество"]

    priority_colors = {
        "red": "#ef553b",
        "yellow": "#fecb52",
        "green": "#00cc96",
        "ignore": "#636efa"
    }

    fig = px.bar(
        priority_counts,
        x="Приоритет",
        y="Количество",
        title="Распределение сообщений по приоритетам",
        color="Приоритет",
        color_discrete_map=priority_colors,
        text="Количество"
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_title="Приоритет",
        yaxis_title="Количество сообщений",
        showlegend=False
    )

    return fig


def create_top_codes_chart(df, top_n=15):
    """
    Топ N кодов ДС по частоте встречаемости
    """
    if df.empty or "messagecode" not in df.columns:
        return None

    top_codes = df["messagecode"].value_counts().head(top_n).reset_index()
    top_codes.columns = ["Код ДС", "Количество"]

    fig = px.bar(
        top_codes,
        x="Количество",
        y="Код ДС",
        orientation="h",
        title=f"Топ-{top_n} кодов ДС",
        text="Количество"
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_title="Количество сообщений",
        yaxis_title="Код ДС",
        height=500
    )

    return fig


def create_hourly_activity_chart(df):
    """
    Активность по часам суток
    """
    if df.empty or "hour" not in df.columns:
        return None

    hourly_counts = df.groupby("hour").size().reset_index(name="count")

    fig = px.line(
        hourly_counts,
        x="hour",
        y="count",
        title="Активность диагностических сообщений по часам",
        markers=True
    )

    fig.update_layout(
        xaxis_title="Час суток",
        yaxis_title="Количество сообщений",
        xaxis=dict(tickmode="linear", tick0=0, dtick=1)
    )

    return fig


def create_daily_timeline_chart(df):
    """
    Динамика сообщений по дням
    """
    if df.empty or "day" not in df.columns:
        return None

    daily_counts = df.groupby("day").size().reset_index(name="count")

    fig = px.line(
        daily_counts,
        x="day",
        y="count",
        title="Динамика сообщений по дням",
        markers=True
    )

    fig.update_layout(
        xaxis_title="Дата",
        yaxis_title="Количество сообщений",
        xaxis=dict(tickangle=45)
    )

    return fig


def create_car_distribution_chart(df, top_n=15):
    """
    Распределение по вагонам
    """
    if df.empty or "carnumber" not in df.columns:
        return None

    # Очистка номеров вагонов
    df_clean = df.copy()
    df_clean["carnumber_clean"] = df_clean["carnumber"].astype(str).fillna("Не указан")

    car_counts = df_clean["carnumber_clean"].value_counts().head(top_n).reset_index()
    car_counts.columns = ["Вагон", "Количество"]

    fig = px.bar(
        car_counts,
        x="Вагон",
        y="Количество",
        title=f"Распределение по вагонам (топ-{top_n})",
        text="Количество"
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_title="Номер вагона",
        yaxis_title="Количество сообщений",
        xaxis=dict(tickangle=45)
    )

    return fig


def create_comparison_chart(df, mode="priority"):
    """
    Сравнение двух поездов
    """
    if df.empty or "train_name_human" not in df.columns:
        return None

    train_names = df["train_name_human"].unique()
    if len(train_names) < 2:
        return None

    if mode == "priority":
        priority_order = {"red": 0, "yellow": 1, "green": 2, "ignore": 3}
        priority_counts = df.groupby(["train_name_human", "priority"]).size().reset_index(name="count")
        priority_counts["priority_order"] = priority_counts["priority"].map(priority_order)
        priority_counts = priority_counts.sort_values("priority_order")

        fig = px.bar(
            priority_counts,
            x="train_name_human",
            y="count",
            color="priority",
            title="Сравнение распределения по приоритетам",
            labels={"train_name_human": "Поезд", "count": "Количество", "priority": "Приоритет"},
            barmode="group",
            color_discrete_map={"red": "#ef553b", "yellow": "#fecb52", "green": "#00cc96", "ignore": "#636efa"}
        )

    elif mode == "hourly":
        hourly_counts = df.groupby(["train_name_human", "hour"]).size().reset_index(name="count")

        fig = px.line(
            hourly_counts,
            x="hour",
            y="count",
            color="train_name_human",
            title="Сравнение почасовой активности",
            labels={"hour": "Час суток", "count": "Количество", "train_name_human": "Поезд"},
            markers=True
        )

    else:
        return None

    return fig


def create_summary_stats(df):
    """
    Сводная статистика
    """
    if df.empty:
        return {
            "total_messages": 0,
            "unique_codes": 0,
            "unique_cars": 0,
            "red_count": 0,
            "yellow_count": 0,
            "green_count": 0,
            "ignore_count": 0,
            "date_range": "Нет данных",
            "trains": []
        }

    stats = {
        "total_messages": len(df),
        "unique_codes": df["messagecode"].nunique() if "messagecode" in df.columns else 0,
        "unique_cars": df["carnumber"].nunique() if "carnumber" in df.columns else 0,
        "red_count": len(df[df["priority"] == "red"]) if "priority" in df.columns else 0,
        "yellow_count": len(df[df["priority"] == "yellow"]) if "priority" in df.columns else 0,
        "green_count": len(df[df["priority"] == "green"]) if "priority" in df.columns else 0,
        "ignore_count": len(df[df["priority"] == "ignore"]) if "priority" in df.columns else 0,
        "date_range": f"{df['timestamp'].min()} - {df['timestamp'].max()}" if "timestamp" in df.columns and not df.empty else "Нет данных",
        "trains": df["train_name_human"].unique().tolist() if "train_name_human" in df.columns else []
    }

    return stats