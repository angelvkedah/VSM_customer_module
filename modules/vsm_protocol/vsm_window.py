import pandas as pd
import streamlit as st
from datetime import datetime
import random

from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode

from modules.vsm_protocol.vsm_help import show_help
from modules.vsm_protocol.vsm_load_data import load_events_data
from modules.vsm_protocol.handlers.decoder import decode_events_df
from modules.vsm_protocol.handlers.timeline_builder import build_timeline
from modules.vsm_protocol.handlers.export import (
    export_to_docx,
    export_human_readable_docx,
    export_to_xlsx,
    export_to_csv,
    export_text_to_docx,
    get_column_names_map,
)
from modules.vsm_protocol.llm.hybrid_protocol_builder import build_hybrid_protocol_text
from modules.vsm_protocol.vsm_ag_grid_options import draw_vsm_table


DEFAULT_COLUMNS = [
    "train_id",
    "carnumber",
    "messagecode",
    "event_type",
    "timestamp",
    "message_text",
]

LLM_LOADING_MESSAGES = [
    "Собираем цифровой след событий...",
    "Секунду... разбираемся, что произошло на борту...",
    "Анализируем. Машинист пока ни при чем...",
    "ИИ раскладывает события по рельсам...",
    "Собираем пазл...",
    "Нейросеть вспоминает, чему ее учили...",
    "ИИ уже пишет объяснительную...",
    "Машина думает... это хороший знак.",
    "Где-то в глубине логов скрывается истина...",
    "Идет декодирование эксплуатационной хроники...",
    "ИИ слушает, о чем шепчутся датчики...",
    "Обнаружены критические события. ИИ напрягся...",
]

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


def _safe_file_part(value):
    """
    Безопасная часть имени файла
    """
    return (
        str(value)
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "-")
    )


def _format_timestamp_for_display(value):
    if pd.isna(value):
        return ""

    try:
        return pd.to_datetime(value).strftime("%d.%m.%Y %H:%M:%S")
    except Exception:
        return str(value)


def _prepare_timeline_for_display(timeline_df, selected_columns):
    """
    Подготавливает таблицу хронологии для отображения
    """
    column_names_map = get_column_names_map()

    available_cols = [
        col for col in selected_columns
        if col in timeline_df.columns
    ]

    display_df = timeline_df[available_cols].copy()

    if "event_type" in display_df.columns:
        event_type_map = {
            "activation": "Активация",
            "deactivation": "Деактивация",
            "still_active_marker": "Активно до сих пор",
        }

        display_df["event_type"] = (
            display_df["event_type"]
            .map(event_type_map)
            .fillna(display_df["event_type"])
        )

    if "timestamp" in display_df.columns:
        display_df["timestamp"] = display_df["timestamp"].apply(
            _format_timestamp_for_display
        )

    display_df = display_df.rename(columns=column_names_map)

    return display_df


def _prepare_raw_events_for_display(events_df):
    """
    Подготавливает сырые сообщения для отображения
    """
    if events_df is None or events_df.empty:
        return pd.DataFrame()

    display_columns = [
        "timestamp",
        "messagecode",
        "message_text",
        "carnumber",
        "messagestate",
        "train_id",
        "parsingtime",
    ]

    existing_columns = [
        col for col in display_columns
        if col in events_df.columns
    ]

    display_df = events_df[existing_columns].copy()

    rename_map = {
        "timestamp": "Время",
        "messagecode": "Код ДС",
        "message_text": "Сообщение",
        "carnumber": "Вагон",
        "messagestate": "Активно",
        "train_id": "Поезд",
        "parsingtime": "Время парсинга",
    }

    if "timestamp" in display_df.columns:
        display_df["timestamp"] = display_df["timestamp"].apply(
            _format_timestamp_for_display
        )

    if "parsingtime" in display_df.columns:
        display_df["parsingtime"] = display_df["parsingtime"].apply(
            _format_timestamp_for_display
        )

    display_df = display_df.rename(columns=rename_map)

    return display_df


def _render_aggrid(df, key, height=500, table_type="default"):
    """
    Отображает DataFrame через AgGrid
    """
    if df is None or df.empty:
        st.info("Нет данных для отображения.")
        return None

    grid_options = draw_vsm_table(
        df,
        page_size=25,
        selection_mode="disabled",
        table_type=table_type,
    )

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        height=height,
        width="100%",
        fit_columns_on_grid_load=True,
        reload_data=True,
        update_mode=GridUpdateMode.NO_UPDATE,
        data_return_mode=DataReturnMode.AS_INPUT,
        allow_unsafe_jscode=True,
        theme="streamlit",
        key=key,
    )

    return grid_response


def _load_one_train(train_id, train_human_name, dt_from, dt_to):
    """
    Загружает события одного поезда и строит хронологию
    """
    events_df = load_events_data(
        train_id=train_id,
        dt_from=dt_from,
        dt_to=dt_to,
        limit=100000,
    )

    if events_df is None or events_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    events_df = decode_events_df(events_df)
    events_df["train_id"] = train_id
    events_df["train_human_name"] = train_human_name

    timeline_df = build_timeline(events_df)

    if timeline_df is not None and not timeline_df.empty:
        timeline_df["train_id"] = train_human_name

    return events_df, timeline_df


def _load_data_for_filters(sidebar_data):
    """
    Загружает данные по текущим фильтрам
    Поддерживает режим одного и двух поездов
    """
    all_events = []
    all_timelines = []

    events_df_1, timeline_df_1 = _load_one_train(
        train_id=sidebar_data.train_id,
        train_human_name=sidebar_data.train_human_name,
        dt_from=sidebar_data.dt_from,
        dt_to=sidebar_data.dt_to,
    )

    if not events_df_1.empty:
        all_events.append(events_df_1)

    if not timeline_df_1.empty:
        all_timelines.append(timeline_df_1)

    if sidebar_data.mode == "Два поезда" and sidebar_data.train_id_2:
        events_df_2, timeline_df_2 = _load_one_train(
            train_id=sidebar_data.train_id_2,
            train_human_name=sidebar_data.train_human_name_2,
            dt_from=sidebar_data.dt_from,
            dt_to=sidebar_data.dt_to,
        )

        if not events_df_2.empty:
            all_events.append(events_df_2)

        if not timeline_df_2.empty:
            all_timelines.append(timeline_df_2)

    if all_events:
        events_df = pd.concat(all_events, ignore_index=True)
    else:
        events_df = pd.DataFrame()

    if all_timelines:
        timeline_df = pd.concat(all_timelines, ignore_index=True)
        timeline_df = timeline_df.sort_values("timestamp").reset_index(drop=True)
    else:
        timeline_df = pd.DataFrame()

    return events_df, timeline_df


def _get_train_name_for_protocol(sidebar_data, timeline_df):
    if sidebar_data.mode == "Два поезда":
        names = [
            sidebar_data.train_human_name,
            sidebar_data.train_human_name_2,
        ]
        names = [name for name in names if name]
        return " и ".join(names)

    return sidebar_data.train_human_name or sidebar_data.train_id


def _render_statistics(events_df, timeline_df):
    with st.expander("Статистика", expanded=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Сырых сообщений", len(events_df))

        with col2:
            unique_codes = (
                timeline_df["messagecode"].nunique()
                if "messagecode" in timeline_df.columns
                else 0
            )
            st.metric("Уникальных кодов ДС", unique_codes)

        with col3:
            unique_cars = (
                timeline_df["carnumber"].nunique()
                if "carnumber" in timeline_df.columns
                else 0
            )
            st.metric("Задействовано вагонов", unique_cars)

        with col4:
            if "deactivation_time" in timeline_df.columns:
                active_count = len(timeline_df[timeline_df["deactivation_time"].isna()])
            else:
                active_count = 0

            st.metric("Активных событий", active_count)


def _render_column_selector():
    column_names_map = get_column_names_map()

    if "vsm_selected_columns" not in st.session_state:
        st.session_state["vsm_selected_columns"] = DEFAULT_COLUMNS

    selected_columns = st.multiselect(
        "Отображаемые колонки",
        options=list(column_names_map.keys()),
        format_func=lambda x: column_names_map.get(x, x),
        default=st.session_state["vsm_selected_columns"],
        key="vsm_selected_columns_widget",
    )

    st.session_state["vsm_selected_columns"] = selected_columns

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Все колонки",
            use_container_width=True,
            key="vsm_select_all_columns",
        ):
            st.session_state["vsm_selected_columns"] = list(column_names_map.keys())
            st.rerun()

    with col2:
        if st.button(
            "Сбросить колонки",
            use_container_width=True,
            key="vsm_reset_columns",
        ):
            st.session_state["vsm_selected_columns"] = DEFAULT_COLUMNS
            st.rerun()

    return st.session_state["vsm_selected_columns"]


def _render_timeline_table(timeline_df):
    with st.expander("Хронология эксплуатационных событий", expanded=True):
        selected_columns = _render_column_selector()

        if not selected_columns:
            st.warning("Не выбрано ни одной колонки для отображения.")
            return

        display_timeline = _prepare_timeline_for_display(
            timeline_df,
            selected_columns,
        )

        st.caption(
            "Таблица поддерживает сортировку, фильтрацию, поиск по колонкам и постраничный просмотр."
        )

        columns_key = "_".join(selected_columns)

        _render_aggrid(
            display_timeline,
            key=f"vsm_timeline_aggrid_{columns_key}",
            height=560,
            table_type="timeline",
        )


def _render_raw_events_table(events_df):
    with st.expander("Диагностические сообщения из БД", expanded=False):
        display_df = _prepare_raw_events_for_display(events_df)

        st.caption(
            "Сырые диагностические сообщения, полученные из базы данных за выбранный период."
        )

        _render_aggrid(
            display_df,
            key="vsm_raw_events_aggrid",
            height=480,
            table_type="raw",
        )


def _render_intelligent_protocol(
    timeline_df,
    train_name_str,
    train_names_for_file,
    sidebar_data,
):
    with st.expander("Интеллектуальное формирование протокола", expanded=False):
        st.markdown(
            """
            Локальная языковая модель формирует развернутое интеллектуальное резюме
            на основе значимых диагностических сообщений.

            В модель передаются только сообщения, отнесённые к важным и критическим,
            а служебные и малозначимые сообщения исключаются предварительной фильтрацией.

            Полученный текст можно вручную отредактировать и скачать в формате DOCX.
            """
        )

        hybrid_state_key = "vsm_hybrid_protocol_text"

        if st.button(
            "Сформировать интеллектуальное резюме",
            type="primary",
            use_container_width=True,
            key="vsm_generate_hybrid_protocol",
        ):
            loading_message = random.choice(LLM_LOADING_MESSAGES)

            with st.spinner(loading_message):
                st.session_state[hybrid_state_key] = build_hybrid_protocol_text(
                    timeline_df=timeline_df,
                    train_name=train_name_str,
                    dt_from=sidebar_data.dt_from,
                    dt_to=sidebar_data.dt_to,
                    max_groups=25,
                )

        if hybrid_state_key in st.session_state:
            edited_hybrid_text = st.text_area(
                "Текст интеллектуального резюме",
                value=st.session_state[hybrid_state_key],
                height=650,
                key="vsm_edited_hybrid_protocol_text",
            )

            hybrid_docx_data = export_text_to_docx(edited_hybrid_text)

            if hybrid_docx_data:
                st.download_button(
                    label="Скачать интеллектуальное резюме (DOCX)",
                    data=hybrid_docx_data,
                    file_name=(
                        f"protocol_intelligent_{train_names_for_file}_"
                        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                    ),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="vsm_download_hybrid_docx",
                )
        else:
            st.info("Нажмите кнопку выше, чтобы сформировать интеллектуальный протокол.")


def _render_export_section(
    timeline_df,
    train_name_str,
    train_names_for_file,
    sidebar_data,
):
    st.markdown("---")
    st.subheader("Экспорт файлов")

    export_options = {
        "DOCX (табличный протокол)": "docx_table",
        "DOCX (списочный протокол)": "docx_human",
        "XLSX": "xlsx",
        "CSV": "csv",
    }

    selected_export_label = st.selectbox(
        "Выберите формат экспорта",
        options=list(export_options.keys()),
        index=0,
        key="vsm_export_format",
    )

    selected_export_type = export_options[selected_export_label]
    timestamp_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
    selected_cols = st.session_state.get("vsm_selected_columns", DEFAULT_COLUMNS)

    export_data = None
    export_file_name = None
    export_mime = None

    if selected_export_type == "docx_table":
        export_data = export_to_docx(
            timeline_df,
            train_name_str,
            sidebar_data.dt_from,
            sidebar_data.dt_to,
            selected_columns=selected_cols,
        )
        export_file_name = f"protocol_table_{train_names_for_file}_{timestamp_suffix}.docx"
        export_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    elif selected_export_type == "docx_human":
        export_data = export_human_readable_docx(
            timeline_df,
            train_name_str,
            sidebar_data.dt_from,
            sidebar_data.dt_to,
            selected_columns=selected_cols,
        )
        export_file_name = f"protocol_human_{train_names_for_file}_{timestamp_suffix}.docx"
        export_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    elif selected_export_type == "xlsx":
        export_data = export_to_xlsx(
            timeline_df,
            train_name_str,
            sidebar_data.dt_from,
            sidebar_data.dt_to,
            selected_columns=selected_cols,
        )
        export_file_name = f"protocol_{train_names_for_file}_{timestamp_suffix}.xlsx"
        export_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    elif selected_export_type == "csv":
        export_data = export_to_csv(
            timeline_df,
            train_name_str,
            sidebar_data.dt_from,
            sidebar_data.dt_to,
            selected_columns=selected_cols,
        )
        export_file_name = f"protocol_{train_names_for_file}_{timestamp_suffix}.csv"
        export_mime = "text/csv"

    if export_data:
        st.download_button(
            label="Скачать протокол",
            data=export_data,
            file_name=export_file_name,
            mime=export_mime,
            use_container_width=True,
            key="vsm_download_protocol_unified",
        )
    else:
        st.error("Ошибка формирования выбранного формата экспорта.")


def vsm_protocol_window(sidebar_data):
    if sidebar_data.help_button:
        show_help()
        return

    st.title("АСФЭП-ДС ВПС")
    st.caption("Автоматизированная система формирования эксплуатационных протоколов")
    st.markdown("---")

    if sidebar_data.error_message:
        st.error(sidebar_data.error_message)
        return

    if not sidebar_data.is_submitted:
        st.info(
            "Выберите поезд(а) и временной интервал на боковой панели, "
            "затем нажмите «Сформировать протокол»."
        )
        return

    current_filter_key = _make_filter_key(sidebar_data)
    previous_filter_key = st.session_state.get("vsm_current_filter_key")

    need_reload = (
        previous_filter_key != current_filter_key
        or "vsm_events_df" not in st.session_state
        or "vsm_timeline_df" not in st.session_state
    )

    if need_reload:
        with st.spinner("Загрузка и обработка диагностических сообщений..."):
            try:
                events_df, timeline_df = _load_data_for_filters(sidebar_data)

                st.session_state["vsm_events_df"] = events_df
                st.session_state["vsm_timeline_df"] = timeline_df
                st.session_state["vsm_current_filter_key"] = current_filter_key

                # При новых фильтрах старый интеллектуальный протокол очищаем
                st.session_state.pop("vsm_hybrid_protocol_text", None)
                st.session_state.pop("vsm_edited_hybrid_protocol_text", None)

            except Exception as e:
                st.error(f"Ошибка при загрузке данных: {e}")
                st.exception(e)
                return

    events_df = st.session_state.get("vsm_events_df", pd.DataFrame())
    timeline_df = st.session_state.get("vsm_timeline_df", pd.DataFrame())

    if events_df.empty:
        st.warning("За выбранный период диагностические сообщения не найдены.")
        return

    if timeline_df.empty:
        st.warning("Хронология событий не сформирована.")
        return

    train_name_str = _get_train_name_for_protocol(sidebar_data, timeline_df)
    train_names_for_file = _safe_file_part(train_name_str)

    st.success(
        f"Загружено {len(events_df)} сообщений, "
        f"построено {len(timeline_df)} записей в хронологии."
    )

    _render_statistics(events_df, timeline_df)
    _render_timeline_table(timeline_df)
    _render_raw_events_table(events_df)
    _render_intelligent_protocol(
        timeline_df=timeline_df,
        train_name_str=train_name_str,
        train_names_for_file=train_names_for_file,
        sidebar_data=sidebar_data,
    )
    _render_export_section(
        timeline_df=timeline_df,
        train_name_str=train_name_str,
        train_names_for_file=train_names_for_file,
        sidebar_data=sidebar_data,
    )