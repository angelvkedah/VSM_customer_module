from datetime import datetime, timedelta

import streamlit as st

from utils.UserClass import User
from modules.vsm_protocol.vsm_load_data import load_trains_data
from modules.vsm_protocol.validators.datetime_range import validate_datetime_range


def get_train_type(train_name, train_desc):
    name_lower = str(train_name).lower()
    desc_lower = str(train_desc).lower()

    if "velaro" in name_lower or "velaro" in desc_lower or "velarorus" in name_lower:
        return "Velaro"

    if "desiro" in name_lower or "desirorus" in name_lower or "эс" in desc_lower:
        return "Desiro"

    return "Другое"


def split_train_series_number(human_name):
    if not human_name:
        return "", ""

    if "-" in human_name:
        series, number = human_name.split("-", 1)
        return series.strip(), number.strip()

    return human_name.strip(), ""


class VSMProtocolSidebar:
    module_name = "vsm_protocol"
    title = "АСФЭП-ДС ВПС"

    def __init__(
        self,
        window_height: int,
        user: User
    ) -> None:
        self.window_height = window_height
        self.user = user

        self.mode = "Один поезд"
        self.train_id = None
        self.train_id_2 = None
        self.train_human_name = None
        self.train_human_name_2 = None
        self.dt_from = None
        self.dt_to = None
        self.is_submitted = False
        self.error_message = None

        self._init_state()

        st.sidebar.header("Параметры фильтрации")

        self._render_mode_selector()
        self._render_train_selectors()
        self._render_datetime_selector()

        st.sidebar.markdown("---")

        self.submit_button = st.sidebar.button(
            "Сформировать протокол",
            type="primary",
            use_container_width=True,
            key="vsm_submit_button"
        )

        self.help_button = st.sidebar.button(
            "Руководство по модулю",
            use_container_width=True,
            key="vsm_help_button"
        )

        if self.submit_button:
            self._validate_and_save_filters()

        saved_filters = st.session_state.get("vsm_submitted_filters")
        if saved_filters:
            self.mode = saved_filters.get("mode")
            self.train_id = saved_filters.get("train_id")
            self.train_id_2 = saved_filters.get("train_id_2")
            self.train_human_name = saved_filters.get("train_human_name")
            self.train_human_name_2 = saved_filters.get("train_human_name_2")
            self.dt_from = saved_filters.get("dt_from")
            self.dt_to = saved_filters.get("dt_to")
            self.is_submitted = True

    def _init_state(self):
        now = datetime.now().replace(microsecond=0)
        default_from = now - timedelta(hours=6)

        defaults = {
            "vsm_mode": "Один поезд",
            "vsm_train_type_1": "Desiro",
            "vsm_train_type_2": "Desiro",
            "vsm_dt_from_date": default_from.date(),
            "vsm_dt_from_time": default_from.time(),
            "vsm_dt_to_date": now.date(),
            "vsm_dt_to_time": now.time(),
            "vsm_submitted_filters": None,
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def _render_mode_selector(self):
        st.sidebar.subheader("Режим анализа")

        self.mode = st.sidebar.radio(
            "Выберите режим",
            options=["Один поезд", "Два поезда"],
            key="vsm_mode",
            horizontal=True,
            help="Можно сформировать протокол по одному поезду или объединённый протокол по двум поездам."
        )

    def _load_grouped_trains(self):
        trains_data = load_trains_data()
        human_to_train_id = trains_data["human_to_train_id"]

        grouped = {
            "Desiro": {},
            "Velaro": {},
            "Другое": {},
        }

        for human_name, train_id in human_to_train_id.items():
            train_type = get_train_type(train_id, human_name)
            grouped.setdefault(train_type, {})
            grouped[train_type][human_name] = train_id

        return grouped

    def _render_train_selectors(self):
        try:
            grouped_trains = self._load_grouped_trains()

            st.sidebar.markdown("---")
            st.sidebar.subheader("Поезд №1")

            self.train_id, self.train_human_name = self._render_single_train_selector(
                grouped_trains=grouped_trains,
                key_prefix="vsm_train_1",
                train_type_key="vsm_train_type_1"
            )

            if self.mode == "Два поезда":
                st.sidebar.markdown("---")
                st.sidebar.subheader("Поезд №2")

                self.train_id_2, self.train_human_name_2 = self._render_single_train_selector(
                    grouped_trains=grouped_trains,
                    key_prefix="vsm_train_2",
                    train_type_key="vsm_train_type_2"
                )
            else:
                self.train_id_2 = None
                self.train_human_name_2 = None

        except Exception as e:
            st.sidebar.error(f"Ошибка загрузки списка поездов: {e}")

            self.train_id = st.sidebar.text_input(
                "Технический ID поезда №1",
                key="vsm_manual_train_id_1",
                placeholder="Например: desirorus_12029"
            )
            self.train_human_name = self.train_id

            if self.mode == "Два поезда":
                self.train_id_2 = st.sidebar.text_input(
                    "Технический ID поезда №2",
                    key="vsm_manual_train_id_2",
                    placeholder="Например: desirorus_12030"
                )
                self.train_human_name_2 = self.train_id_2

    def _render_single_train_selector(
        self,
        grouped_trains,
        key_prefix,
        train_type_key
    ):
        selected_type = st.sidebar.radio(
            "Тип поезда",
            options=["Desiro", "Velaro"],
            key=train_type_key,
            horizontal=True
        )

        available_trains = grouped_trains.get(selected_type, {})

        if not available_trains:
            st.sidebar.warning(f"Нет доступных поездов типа {selected_type}")
            return None, None

        if selected_type == "Desiro":
            series_to_numbers = {}

            for human_name in available_trains.keys():
                series, number = split_train_series_number(human_name)

                if not series:
                    continue

                if series not in series_to_numbers:
                    series_to_numbers[series] = []

                if number and number not in series_to_numbers[series]:
                    series_to_numbers[series].append(number)

            series_list = sorted(series_to_numbers.keys())

            selected_series = st.sidebar.selectbox(
                "Серия поезда",
                options=series_list,
                key=f"{key_prefix}_series"
            )

            numbers = sorted(series_to_numbers.get(selected_series, []))

            selected_number = st.sidebar.selectbox(
                "Номер поезда",
                options=numbers,
                key=f"{key_prefix}_number"
            )

            selected_human_name = f"{selected_series}-{selected_number}"

        else:
            velaro_options = sorted(available_trains.keys())

            selected_human_name = st.sidebar.selectbox(
                "Выберите поезд Velaro",
                options=velaro_options,
                key=f"{key_prefix}_velaro"
            )

        selected_train_id = available_trains.get(selected_human_name)

        st.sidebar.caption(f"Выбран поезд: **{selected_human_name}**")

        return selected_train_id, selected_human_name

    def _render_datetime_selector(self):
        st.sidebar.markdown("---")
        st.sidebar.subheader("Временной интервал")

        dt_from_date = st.sidebar.date_input(
            "Дата начала",
            key="vsm_dt_from_date"
        )

        dt_from_time = st.sidebar.time_input(
            "Время начала",
            key="vsm_dt_from_time"
        )

        dt_to_date = st.sidebar.date_input(
            "Дата окончания",
            key="vsm_dt_to_date"
        )

        dt_to_time = st.sidebar.time_input(
            "Время окончания",
            key="vsm_dt_to_time"
        )

        self.dt_from = datetime.combine(dt_from_date, dt_from_time)
        self.dt_to = datetime.combine(dt_to_date, dt_to_time)

    def _validate_and_save_filters(self):
        if not self.train_id:
            self.error_message = "Не выбран поезд №1"
            self.is_submitted = False
            return

        if self.mode == "Два поезда" and not self.train_id_2:
            self.error_message = "Не выбран поезд №2"
            self.is_submitted = False
            return

        is_valid, error_text = validate_datetime_range(
            self.dt_from,
            self.dt_to
        )

        if not is_valid:
            self.error_message = error_text
            self.is_submitted = False
            return

        filters = {
            "mode": self.mode,
            "train_id": self.train_id,
            "train_id_2": self.train_id_2 if self.mode == "Два поезда" else None,
            "train_human_name": self.train_human_name,
            "train_human_name_2": self.train_human_name_2 if self.mode == "Два поезда" else None,
            "dt_from": self.dt_from,
            "dt_to": self.dt_to,
        }

        st.session_state["vsm_submitted_filters"] = filters

        self.mode = filters["mode"]
        self.train_id = filters["train_id"]
        self.train_id_2 = filters["train_id_2"]
        self.train_human_name = filters["train_human_name"]
        self.train_human_name_2 = filters["train_human_name_2"]
        self.dt_from = filters["dt_from"]
        self.dt_to = filters["dt_to"]
        self.is_submitted = True
        self.error_message = None