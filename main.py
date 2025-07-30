import streamlit as st

from utils.firebase_utils import get_all_barber_ids, get_barber_config

# --- Handle barber ID from URL ---
query_params = st.query_params
barber_id = query_params.get("barber", "default_barber")

# Load the barber config
config = get_barber_config(barber_id)

st.set_page_config(page_title="Barber Queue Tracker", layout="centered")
st.title("💈 Welcome to the Barber Queue App")

st.markdown("""
This app helps manage both **walk-ins** and **booked appointments** seamlessly.

### 🖥️ Kiosk View *(Public Display)*
- Join the queue as a walk-in  
- See live wait times without showing names  
- Confirm your queue position instantly  

### 🔐 Admin Panel *(PIN Protected)*
- View a unified queue of walk-ins and bookings  
- Tick off customers as they’re served  
- Export daily logs as CSV  

### 📅 Book Appointment
- Customers can pre-book time slots  
- Prevents overbooking and reduces wait times  

### 📊 Dashboard *(Public Display)*
- Track daily usage trends  
- Compare bookings vs walk-ins  
- View queue sizes and estimated wait times  

👉🏿 Use the sidebar to switch between pages.  
Let’s make queueing smarter, smoother, and stress-free! 💇🏿‍‍✨💇🏿‍♀️
""")

# --- Page Setup ---
st.set_page_config(page_title="Barber Selector", layout="centered")
st.title("💈 Choose Your Barber")

# --- Barber Selection ---
barber_ids = get_all_barber_ids()
selected_barber = st.selectbox("Select a Barber:", barber_ids)

if selected_barber:
    config = get_barber_config(selected_barber)
    logo_url = config.get("logo_url", "")

    if logo_url:
        st.image(logo_url, width=200)

    st.markdown(f"### Welcome to **{selected_barber.replace('_', ' ').title()}**!")

    st.divider()
    st.markdown("#### 📍 Choose a section:")

    # --- Buttons to Navigate ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🖥️ Kiosk View"):
            st.experimental_set_query_params(barber=selected_barber)
            st.switch_page("pages/1_Kiosk.py")
        if st.button("📊 Dashboard"):
            st.experimental_set_query_params(barber=selected_barber)
            st.switch_page("pages/3_Dashboard.py")

    with col2:
        if st.button("🔐 Admin Panel"):
            st.experimental_set_query_params(barber=selected_barber)
            st.switch_page("pages/2_Admin.py")
        if st.button("📅 Book Appointment"):
            st.experimental_set_query_params(barber=selected_barber)
            st.switch_page("pages/4_Book_Appointment.py")