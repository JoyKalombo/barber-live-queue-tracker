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
