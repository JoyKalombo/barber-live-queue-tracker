import streamlit as st
from utils.firebase_utils import get_barber_config
from utils.session import get_barber_id, set_barber_id

st.set_page_config(page_title="Barber Portal", layout="centered")

barber_id = get_barber_id()
config = get_barber_config(barber_id)

st.title(f"💈 {config.get('shop_name', barber_id.replace('_', ' ').title())}")

if logo := config.get("logo_url", ""):
    st.image(logo, width=200)

with st.expander("ℹ️ What does each option do?"):
    st.markdown(f"""
    This app helps manage both **walk-ins** and **booked appointments** seamlessly at **{barber_id}**.

    ### 🖥️ Kiosk View *(Public Display)*
    - 🧍🏾 Join the queue as a walk-in  
    - ⏳ See live wait times without showing names  
    - ✅ Confirm your queue position instantly  

    ### 🔐 Admin Panel *(PIN Protected)*
    - 📋 View a unified queue of walk-ins and bookings  
    - ☑️ Tick off customers as they’re served  
    - 🧾 Export daily logs as CSV  

    ### 📅 Book Appointment
    - 📆 Customers can pre-book time slots  
    - 🚫 Prevents overbooking and reduces wait times  

    ### 📊 Dashboard *(Public Display)*
    - 📈 Track daily usage trends  
    - 🔄 Compare bookings vs walk-ins  
    - ⏱️ View queue sizes and estimated wait times  

    👉🏿 Use the sidebar or the buttons below to get started.  
    Let’s make queueing smarter, smoother, and stress-free! 💇🏿‍‍✨💇🏿‍♀️
    """)


st.markdown("#### 📍 Choose an option:")

col1, col2 = st.columns(2)

with col1:
    if st.button("🖥️ Kiosk View"):
        set_barber_id(barber_id)        # ensure URL/session updated
        st.switch_page("pages/1_Kiosk_View.py")

    if st.button("📊 Dashboard"):
        set_barber_id(barber_id)        # ensure URL/session updated
        st.switch_page("pages/3_Dashboard.py")

with col2:
    if st.button("🔐 Admin Panel"):
        set_barber_id(barber_id)        # ensure URL/session updated
        st.switch_page("pages/2_Admin_Panel.py")

    if st.button("📅 Book Appointment"):
        set_barber_id(barber_id)        # ensure URL/session updated
        st.switch_page("pages/4_Book_Appointment.py")
