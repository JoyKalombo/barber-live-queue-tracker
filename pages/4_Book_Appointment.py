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
close_time = datetime.now().replace(hour=22, minute=0, second=0, microsecond=0)

st.set_page_config(page_title="Book Appointment", layout="centered")
st.title("📅 Book an Appointment")

# Add this near the top with the other now-related variables
today = datetime.now().date()

# --- Booking Form ---
st.subheader("🗓️ Select Date for Booking")
selected_date = st.date_input("Pick a date:", min_value=today)

# Only show time slots if a date is selected
if selected_date:
    # Recalculate today's current time without seconds/milliseconds
    now = datetime.now().replace(second=0, microsecond=0)

    # Adjust open/close time for selected day
    open_time = datetime.combine(selected_date, datetime.min.time()).replace(hour=10)
    close_time = datetime.combine(selected_date, datetime.min.time()).replace(hour=22)

    walkins = walkin_ref.get() or {}
    bookings = booking_ref.get() or {}

    sorted_walkins = sorted(walkins.items(), key=lambda x: x[1]["joined_at"])
    sorted_bookings = sorted(bookings.items(), key=lambda x: x[1]["slot"])

    # --- Generate blocked time ranges ---
    blocked_slots = []

    # Block out walk-ins only if selected_date is today
    if selected_date == today:
        walkin_start = open_time
        for _ in sorted_walkins:
            blocked_slots.append((walkin_start, walkin_start + timedelta(minutes=avg_cut_duration)))
            walkin_start += timedelta(minutes=avg_cut_duration)

    # Block out bookings on selected date
    for _, b in sorted_bookings:
        slot_dt = datetime.fromisoformat(b["slot"])
        if slot_dt.date() == selected_date:
            blocked_slots.append((slot_dt, slot_dt + timedelta(minutes=avg_cut_duration)))

    # --- Generate available slots ---
    available_slots = []
    slot = open_time
    while slot + timedelta(minutes=avg_cut_duration) <= close_time:
        if selected_date == today and slot < now:
            slot += timedelta(minutes=avg_cut_duration)
            continue
        overlap = any(bs <= slot < be or (slot <= bs < slot + timedelta(minutes=avg_cut_duration))
                      for bs, be in blocked_slots)
        if not overlap:
            available_slots.append(slot)
        slot += timedelta(minutes=avg_cut_duration)

    # --- Booking Form ---
    if available_slots:
        with st.form("booking_form"):
            name = st.text_input("Enter your full name:")
            chosen_slot = st.selectbox(
                "Pick an available time:",
                [s.strftime('%H:%M') for s in available_slots]
            )
            submit = st.form_submit_button("📥 Confirm Booking")

            if submit and name.strip():
                selected_time = next(s for s in available_slots if s.strftime('%H:%M') == chosen_slot)

                # Save to Firebase
                booking_ref.push({
                    "name": name.strip().title(),
                    "slot": selected_time.isoformat()
                })

                st.session_state["booking_confirmation"] = {
                    "name": name.strip().title(),
                    "datetime": selected_time.isoformat()
                }
                st.rerun()
    else:
        st.info("🕒 No appointment slots available for this date.")

# --- Show confirmation if booking was successful ---
if "booking_confirmation" in st.session_state:
    confirm = st.session_state["booking_confirmation"]
    booked_dt = datetime.fromisoformat(confirm["datetime"])
    booked_day = booked_dt.strftime("%A %d %B %Y")
    booked_time = booked_dt.strftime("%H:%M")

    st.success(
        f"✅ {confirm['name']}, your booking has been made!\n\n"
        f"📅 Date: **{booked_day}**\n\n"
        f"🕒 Time: **{booked_time}**"
    )