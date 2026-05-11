from st_aggrid import GridOptionsBuilder, JsCode


def draw_vsm_table(
    df,
    page_size=25,
    selection_mode="disabled",
    table_type="default"
):
    """
    Формирует настройки AgGrid для таблиц модуля АСФЭП-ДС ВПС.
    """

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(
        resizable=True,
        filterable=True,
        sortable=True,
        editable=False,
        groupable=True,
        min_column_width=110,
        wrapText=True,
        autoHeight=True,
    )

    # Подсветка строк по типу события
    event_type_row_style = JsCode("""
    function(params) {
        const eventType = params.data['Тип события'];

        if (eventType === 'Активация') {
            return {
                'background-color': '#fff7e6'
            };
        }

        if (eventType === 'Деактивация') {
            return {
                'background-color': '#eef8ee'
            };
        }

        if (eventType === 'Активно до сих пор') {
            return {
                'background-color': '#ffecec',
                'font-weight': '600'
            };
        }

        return {};
    }
    """)

    # Подсветка колонки кода ДС
    if "Код ДС" in df.columns:
        gb.configure_column(
            "Код ДС",
            header_name="Код ДС",
            width=120,
            pinned="left",
            filter=True,
        )

    if "Время события" in df.columns:
        gb.configure_column(
            "Время события",
            header_name="Время события",
            width=190,
            pinned="left",
            sort="asc",
        )

    if "Номер поезда" in df.columns:
        gb.configure_column(
            "Номер поезда",
            header_name="Поезд",
            width=140,
            pinned="left",
        )

    if "Вагон" in df.columns:
        gb.configure_column(
            "Вагон",
            header_name="Вагон",
            width=110,
        )

    if "Тип события" in df.columns:
        gb.configure_column(
            "Тип события",
            header_name="Тип события",
            width=150,
        )

    if "Описание" in df.columns:
        gb.configure_column(
            "Описание",
            header_name="Описание диагностического сообщения",
            width=520,
            wrapText=True,
            autoHeight=True,
        )

    if "Сообщение" in df.columns:
        gb.configure_column(
            "Сообщение",
            header_name="Сообщение",
            width=520,
            wrapText=True,
            autoHeight=True,
        )

    gb.configure_pagination(
        enabled=True,
        paginationPageSize=page_size,
        paginationAutoPageSize=False,
    )

    if selection_mode != "disabled":
        gb.configure_selection(
            selection_mode=selection_mode,
            use_checkbox=False,
        )

    gb.configure_grid_options(
        rowHeight=42,
        headerHeight=48,
        suppressHorizontalScroll=False,
        alwaysShowHorizontalScroll=True,
        suppressColumnVirtualisation=False,
        enableRangeSelection=True,
        animateRows=False,
        rowSelection=selection_mode,
        getRowStyle=event_type_row_style if table_type == "timeline" else None,
        domLayout="normal",
    )

    return gb.build()