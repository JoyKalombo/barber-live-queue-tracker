# utils/session.py
import streamlit as st

BARBER_KEY = "barber_id"


def set_barber_id(barber_id: str) -> None:
    """Persist barber_id in session and sync URL."""
    st.session_state[BARBER_KEY] = barber_id
    # Always try to sync the URL for sharing/refreshing
    try:
        st.query_params["barber"] = barber_id
    except Exception:
        pass  # Fails if called from switch_page, but that's fine.


def get_barber_id(default: str = "default_barber") -> str:
    """
    Retrieves the barber_id, prioritizing session state.
    On first load, it will use the URL or a default value.
    """
    # 1) If the barber ID is already in the session, use that.
    if BARBER_KEY in st.session_state and st.session_state[BARBER_KEY]:
        return st.session_state[BARBER_KEY]

    # 2) On initial app load (session state is empty), check the URL.
    barber_from_url = st.query_params.get("barber")
    if barber_from_url:
        st.session_state[BARBER_KEY] = barber_from_url
        return barber_from_url

    # 3) Fallback to default
    st.session_state[BARBER_KEY] = default
    try:
        st.query_params["barber"] = default
    except Exception:
        pass
    return default
