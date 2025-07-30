import streamlit as st

from utils.firebase_utils import get_all_barber_ids, get_barber_config


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

# main.py

st.set_page_config(page_title="Barber Selector", layout="centered")
st.title("💈 Choose Your Barber")

# --- Handle barber ID from URL ---
query_params = st.query_params
barber_id = query_params.get("barber", "default_barber")

# Load the barber config
config = get_barber_config(barber_id)

# Get all barber IDs
barber_ids = get_all_barber_ids()  # <-- We'll define this in firebase_utils

selected_barber = st.selectbox("Select a Barber:", barber_ids)

if selected_barber:
    config = get_barber_config(selected_barber)
    st.image(config.get("logo_url", ""), width=200)
    st.markdown(f"### Welcome to **{selected_barber.replace('_', ' ').title()}**!")

    st.markdown("#### 📍 Choose a section:")
    st.page_link("pages/1_Kiosk.py", label="Kiosk View", params={"barber": selected_barber})
    st.page_link("pages/2_Admin.py", label="Admin Panel", params={"barber": selected_barber})
    st.page_link("pages/3_Dashboard.py", label="Dashboard", params={"barber": selected_barber})
    st.page_link("pages/4_Book_Appointment.py", label="Book Appointment", params={"barber": selected_barber})
