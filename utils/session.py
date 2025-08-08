import streamlit as st

BARBER_KEY = "barber_id"


def set_barber_id(barber_id: str) -> None:
    """Persist barber_id in both session state and URL query string."""
    st.session_state[BARBER_KEY] = barber_id
    st.query_params["barber"] = barber_id  # ensure it's in the URL


def get_barber_id(default: str = "default_barber") -> str:
    """
    Resolve the current barber_id, preferring the URL (?barber=...),
    then session_state, keeping them in sync. Falls back to default.
    """
    # Prefer URL
    barber_from_url = st.query_params.get("barber")
    if barber_from_url:
        st.session_state[BARBER_KEY] = barber_from_url
        return barber_from_url

    # Else try session
    barber_from_session = st.session_state.get(BARBER_KEY)
    if barber_from_session:
        st.query_params["barber"] = barber_from_session
        return barber_from_session

    # Else default
    st.session_state[BARBER_KEY] = default
    st.query_params["barber"] = default
    return default


def get_barber_context(default: str = "default_barber"):
    """Return (barber_id, config) for the current barber."""
    from utils.firebase_utils import get_barber_config
    barber_id = get_barber_id(default)
    return barber_id, get_barber_config(barber_id)
