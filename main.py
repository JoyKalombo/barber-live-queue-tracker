import streamlit as st

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