import streamlit as st
from utils.firebase_utils import get_all_barber_ids

st.set_page_config(page_title="Choose Your Barber", layout="centered")

st.title("💈 Welcome to the Barber Queue App")
st.markdown("Please select your barber shop:")

barber_ids = get_all_barber_ids()

selected = st.selectbox("Barber:", barber_ids)

if selected:
    if st.button("Go to Barber Portal"):
        st.query_params["barber"] = selected
        st.switch_page("pages/barber_main.py")