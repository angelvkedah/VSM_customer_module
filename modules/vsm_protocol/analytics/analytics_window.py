import pandas as pd
import streamlit as st

from modules.vsm_protocol.analytics.analytics_help import show_analytics_help
from modules.vsm_protocol.analytics.analytics_load_data import load_analytics_data_for_filters
from modules.vsm_protocol.analytics.charts import (
    create_priority_distribution_chart,
    create_top_codes_chart,
    create_hourly_activity_chart,
    create_daily_timeline_chart,
    create_car_distribution_chart,
    create_comparison_chart,
    create_summary_stats,
)


def _make_filter_key(sidebar_data):
    """
    Формирует ключ текущих фильтров
    """
    return (
        sidebar_data.mode,
        sidebar_data.train_id,
        sidebar_data.train_id_2,
        sidebar_data.dt_from,
        sidebar_data.dt_to,
    )


def analytics_window(sidebar_data):
    if sidebar_data.help_button:
        show_analytics_help()
        return

    st.title("📊 Аналитика диагностических сообщений")
    st.caption("Визуализация и анализ диагностических данных")
    st.markdown("---")

    if sidebar_data.error_message:
        st.error(sidebar_data.error_message)
        return

    if not sidebar_data.is_submitted:
        st.info(
            "Выберите поезд(а) и временной интервал на боковой панели, "
            "затем нажмите «Построить аналитику»."
        )
        return

    current_filter_key = _make_filter_key(sidebar_data)
    previous_filter_key = st.session_state.get("analytics_current_filter_key")

    need_reload = (
        previous_filter_key != current_filter_key
        or "analytics_df" not in st.session_state
    )

    if need_reload:
        # Очищаем старые данные
        for key in ["analytics_df", "analytics_current_filter_key"]:
            if key in st.session_state:
                del st.session_state[key]

        with st.spinner("Загрузка и обработка данных для аналитики..."):
            try:
                df = load_analytics_data_for_filters(sidebar_data)

                st.session_state["analytics_df"] = df
                st.session_state["analytics_current_filter_key"] = current_filter_key

                st.rerun()

            except Exception as e:
                st.error(f"Ошибка при загрузке данных: {e}")
                st.exception(e)
                return

        return

    df = st.session_state.get("analytics_df", pd.DataFrame())

    if df.empty:
        st.warning("За выбранный период диагностические сообщения не найдены.")
        return

    # Сводная статистика
    stats = create_summary_stats(df)

    st.success(
        f"📊 Загружено **{stats['total_messages']}** диагностических сообщений "
        f"за период с {sidebar_data.dt_from.strftime('%d.%m.%Y %H:%M')} "
        f"по {sidebar_data.dt_to.strftime('%d.%m.%Y %H:%M')}"
    )

    # Карточки с ключевыми метриками
    st.subheader("Ключевые метрики")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Всего сообщений", stats["total_messages"])

    with col2:
        st.metric("Уникальных кодов ДС", stats["unique_codes"])

    with col3:
        st.metric("Задействовано вагонов", stats["unique_cars"])

    with col4:
        st.metric(
            "Критические (красные)",
            stats["red_count"],
            delta_color="inverse"
        )

    with col5:
        st.metric(
            "Значимые (жёлтые)",
            stats["yellow_count"]
        )

    st.markdown("---")

    # Графики
    st.subheader("Визуализация данных")

    # Распределение по приоритетам
    col1, col2 = st.columns(2)

    with col1:
        priority_chart = create_priority_distribution_chart(df)
        if priority_chart:
            st.plotly_chart(priority_chart, use_container_width=True)
        else:
            st.info("Нет данных для отображения распределения по приоритетам")

    with col2:
        top_codes_chart = create_top_codes_chart(df)
        if top_codes_chart:
            st.plotly_chart(top_codes_chart, use_container_width=True)
        else:
            st.info("Нет данных для отображения топа кодов ДС")

    st.markdown("---")

    # Временные графики
    col1, col2 = st.columns(2)

    with col1:
        hourly_chart = create_hourly_activity_chart(df)
        if hourly_chart:
            st.plotly_chart(hourly_chart, use_container_width=True)
        else:
            st.info("Нет данных для отображения почасовой активности")

    with col2:
        daily_chart = create_daily_timeline_chart(df)
        if daily_chart:
            st.plotly_chart(daily_chart, use_container_width=True)
        else:
            st.info("Нет данных для отображения динамики по дням")

    st.markdown("---")

    # Распределение по вагонам
    st.subheader("Распределение по вагонам")
    car_chart = create_car_distribution_chart(df)
    if car_chart:
        st.plotly_chart(car_chart, use_container_width=True)
    else:
        st.info("Нет данных для отображения распределения по вагонам")

    # Сравнение поездов (если выбрано два)
    if sidebar_data.mode == "Два поезда" and sidebar_data.train_id_2:
        st.markdown("---")
        st.subheader("Сравнение поездов")

        col1, col2 = st.columns(2)

        with col1:
            comparison_priority = create_comparison_chart(df, mode="priority")
            if comparison_priority:
                st.plotly_chart(comparison_priority, use_container_width=True)
            else:
                st.info("Нет данных для сравнения по приоритетам")

        with col2:
            comparison_hourly = create_comparison_chart(df, mode="hourly")
            if comparison_hourly:
                st.plotly_chart(comparison_hourly, use_container_width=True)
            else:
                st.info("Нет данных для сравнения почасовой активности")

    # Таблица с данными (опционально)
    st.markdown("---")
    with st.expander("Показать сырые данные"):
        st.dataframe(df, use_container_width=True)