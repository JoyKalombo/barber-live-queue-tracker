# utils/session.py
import streamlit as st

# utils/session.py
from utils.firebase_utils import get_barber_config


def get_barber_id(default="default_barber"):
    barber = st.query_params.get("barber")
    if not barber:
        st.warning("⚠️ No barber selected. Returning to default.")
        return default
    return barber


def get_barber_context(default="default_barber"):
    barber_id = st.query_params.get("barber", default)
    config = get_barber_config(barber_id)
    return barber_id, config


_KEY = "barber_id"


def set_barber_id(barber_id: str) -> None:
    st.session_state[_KEY] = barber_id
    # set URL param too (new API, not experimental)
    st.query_params["barber"] = barber_id


def get_barber_id(default: str = "default_barber") -> str:
    # URL wins, then session, then default
    return st.query_params.get("barber", st.session_state.get(_KEY, default))
