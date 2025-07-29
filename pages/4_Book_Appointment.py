import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh

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

# Show success message if booking just happened
if "booking_confirmation" in st.session_state:
    booking = st.session_state["booking_confirmation"]
    dt = datetime.fromisoformat(booking["datetime"]).astimezone(ZoneInfo("Europe/London"))
    formatted_dt = dt.strftime("%A %d %B at %I:%M %p")
    st.success(f"✅ {booking['name']}, your booking is confirmed for {formatted_dt}.")

# Showcasing the current date and time
today = datetime.now().date()

# --- Booking Form ---
st.subheader("🗓️ Select Date for Booking")
selected_date = st.date_input("Pick a date:", min_value=today)

# Only show time slots if a date is selected
if selected_date:
    # Recalculate today's current time without seconds/milliseconds
    tz = ZoneInfo("Europe/London")
    now = datetime.now(tz).replace(second=0, microsecond=0)

    # Adjust open/close time for selected day
    tz = ZoneInfo("Europe/London")
    open_time = datetime.combine(selected_date, datetime.min.time(), tzinfo=tz).replace(hour=10)
    close_time = datetime.combine(selected_date, datetime.min.time(), tzinfo=tz).replace(hour=22)

    walkins = walkin_ref.get() or {}
    bookings = booking_ref.get() or {}

    sorted_walkins = sorted(
        [(k, v) for k, v in walkins.items() if "joined_at" in v],
        key=lambda x: x[1]["joined_at"]
    )

    sorted_bookings = sorted(
        [(k, v) for k, v in bookings.items() if "slot" in v],
        key=lambda x: x[1]["slot"]
    )

    # --- Generate blocked time ranges ---
    blocked_slots = []

    # Block out walk-ins only if selected_date is today
    if selected_date == today:
        walkin_queue = [
            datetime.fromisoformat(v["joined_at"]).replace(tzinfo=tz)
            for k, v in sorted_walkins
            if "joined_at" in v and datetime.fromisoformat(v["joined_at"]).date() == selected_date
        ]

        # Start from open_time or now (whichever is later)
        walkin_start = max(open_time, now)
        for _ in walkin_queue:
            blocked_slots.append((walkin_start, walkin_start + timedelta(minutes=avg_cut_duration)))
            walkin_start += timedelta(minutes=avg_cut_duration)

    # Block out bookings on selected date
    for _, b in sorted_bookings:
        slot_dt = datetime.fromisoformat(b["slot"]).replace(tzinfo=ZoneInfo("Europe/London"))
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