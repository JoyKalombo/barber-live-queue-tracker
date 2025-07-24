import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import pytz

# --- Firebase init (singleton) ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {'databaseURL': st.secrets["firebase_db_url"]})

walkin_ref = db.reference("walkins")
booking_ref = db.reference("bookings")
avg_cut_duration = 25  # in minutes
open_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
close_time = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)

st.set_page_config(page_title="Book Appointment", layout="centered")
st.title("📅 Book an Appointment")

if "booking_confirmation" in st.session_state:
    msg = st.session_state["booking_confirmation"]
    st.success(
        f"✅ {msg['name']}, your appointment at **{msg['time']}** has been booked!"
    )
    if st_autorefresh(interval=20_000, limit=1, key="clear_booking_confirm"):
        del st.session_state["booking_confirmation"]

# --- Get existing walk-ins and bookings ---
now = datetime.now()
walkins = walkin_ref.get() or {}
bookings = booking_ref.get() or {}

sorted_walkins = sorted(walkins.items(), key=lambda x: x[1]["joined_at"])
sorted_bookings = sorted(bookings.items(), key=lambda x: x[1]["slot"])

# --- Generate blocked time ranges ---
blocked_slots = []

# Block out walk-ins sequentially from open_time
walkin_start = open_time
for _ in sorted_walkins:
    blocked_slots.append((walkin_start, walkin_start + timedelta(minutes=avg_cut_duration)))
    walkin_start += timedelta(minutes=avg_cut_duration)

# Block out fixed bookings
for _, b in sorted_bookings:
    slot_time = datetime.fromisoformat(b["slot"])
    blocked_slots.append((slot_time, slot_time + timedelta(minutes=avg_cut_duration)))

# --- Generate all possible slots ---
available_slots = []
slot = open_time
while slot + timedelta(minutes=avg_cut_duration) <= close_time:
    overlap = any(
        bs <= slot < be or (slot <= bs < slot + timedelta(minutes=avg_cut_duration))
        for bs, be in blocked_slots
    )
    if not overlap:
        available_slots.append(slot)
    slot += timedelta(minutes=avg_cut_duration)

# --- Booking Form ---
if available_slots:
    with st.form("booking_form"):
        name = st.text_input("Enter your full name:")
        chosen_slot = st.selectbox("Pick an available time:", [s.strftime('%H:%M') for s in available_slots])
        submit = st.form_submit_button("📥 Confirm Booking")

        if submit and name.strip():
            # Parse slot back to datetime
            selected_time = next(s for s in available_slots if s.strftime('%H:%M') == chosen_slot)

            # Save to Firebase
            booking_ref.push({
                "name": name.strip().title(),
                "slot": selected_time.isoformat()
            })

            st.session_state["booking_confirmation ✅ "] = {
                "name": name,
                "time": selected_time.strftime('%H:%M')
            }
            st.rerun()

else:
    st.info("🕒 No appointment slots available today.")