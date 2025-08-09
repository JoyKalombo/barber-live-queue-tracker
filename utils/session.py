import streamlit as st

BARBER_KEY = "barber_id"


def set_barber_id(barber_id: str) -> None:
    """Persist barber_id in session; URL can be synced later."""
    st.session_state[BARBER_KEY] = barber_id
    st.write(f"Barber ID set to: {st.session_state[BARBER_KEY]}")  # Debugging line


def get_barber_id(default: str = "default_barber") -> str:
    """
    Prefer session (since switch_page clears the URL),
    then URL if present, then default. After resolving,
    sync the URL so refresh/share still works.
    """
    # 1) Prefer session (most reliable across switch_page)
    if BARBER_KEY in st.session_state and st.session_state[BARBER_KEY]:
        current = st.session_state[BARBER_KEY]
        # keep URL in sync
        try:
            st.query_params["barber"] = current
        except Exception:
            pass
        return current

    # 2) Else try URL
    barber_from_url = st.query_params.get("barber")
    if barber_from_url:
        st.session_state[BARBER_KEY] = barber_from_url
        return barber_from_url

    # 3) Fallback to default and sync both
    st.session_state[BARBER_KEY] = default
    try:
        st.query_params["barber"] = default
    except Exception:
        pass
    return default
