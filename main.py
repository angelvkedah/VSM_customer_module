import streamlit as st

from utils.UserClass import User
from modules.vsm_protocol.vsm_sidebar import VSMProtocolSidebar
from modules.vsm_protocol.vsm_window import vsm_protocol_window


st.set_page_config(
    page_title="АСФЭП-ДС ВПС",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded"
)


BUILDER_MODULES = {
    "АСФЭП-ДС ВПС": {
        "sidebar": VSMProtocolSidebar,
        "window": vsm_protocol_window,
    }
}


def main():
    selected_module = st.sidebar.selectbox(
        "Выберите модуль",
        options=list(BUILDER_MODULES.keys())
    )

    module_config = BUILDER_MODULES[selected_module]

    user = User()
    window_height = 900

    sidebar_data = module_config["sidebar"](
        window_height=window_height,
        user=user
    )

    module_config["window"](sidebar_data)


if __name__ == "__main__":
    main()