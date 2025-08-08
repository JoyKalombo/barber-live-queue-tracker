import streamlit as st
from utils.firebase_utils import get_all_barber_ids
from utils.session import set_barber_id

st.set_page_config(page_title="Choose Your Barber", layout="centered")

st.title("💈 Welcome to the Barber Queue App")
st.markdown("Please select your barber shop:")

barber_ids = get_all_barber_ids()
selected = st.selectbox("Barber:", barber_ids)

if selected and st.button("Go to Barber Portal"):
    set_barber_id(selected)
    st.switch_page(f"pages/barber_main.py?barber={selected}")

