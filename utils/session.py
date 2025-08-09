# utils/session.py
# utils/session.py
import streamlit as st

BARBER_KEY = "barber_id"


def set_barber_id(barber_id: str) -> None:
    """Persist barber_id in session."""
    st.session_state[BARBER_KEY] = barber_id


def get_barber_id(default: str = "default_barber") -> str:
    """
    Retrieves the barber_id, prioritizing session state.
    On first load, it will use the URL or a default value.
    """
    # Prefer session state first
    if BARBER_KEY in st.session_state:
        return st.session_state[BARBER_KEY]

    # If not in session, check the URL
    barber_from_url = st.query_params.get("barber")
    if barber_from_url:
        set_barber_id(barber_from_url)  # Set it to session for future use
        return barber_from_url

    # Fallback to default
    set_barber_id(default)  # Set default to session
    return default