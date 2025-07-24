import streamlit as st

st.set_page_config(page_title="Barber Queue Tracker", layout="centered")
st.title("💈 Welcome to the Barber Queue App")

st.markdown("""
This app has three views:
- **Kiosk View** (public display): see live wait times without revealing names
- **Admin Panel** (PIN protected): manage queue, mark people as done
- **Dashboard page** (public display): see dashboard of usage stats ) daily queue count, average wait time)

👉 Use the sidebar to switch views.
""")