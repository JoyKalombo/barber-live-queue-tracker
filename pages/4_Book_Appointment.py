import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh

from utils.firebase_utils import get_barber_config

# Load the barber config
barber_id = st.query_params.get("barber", "default_barber")  # fallback to "default_barber"
config = get_barber_config(barber_id)

shop_name = config.get("shop_name", "Unknown Barber")
open_hour = config.get("open_hour", 10)
close_hour = config.get("close_hour", 22)
avg_cut_duration = config.get("avg_cut_duration", 25)
logo_url = config.get("logo_url")

# --- Firebase init (singleton) ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {'databaseURL': st.secrets["firebase_db_url"]})

# --- Handle barber ID from URL ---
query_params = st.experimental_get_query_params()
barber_id = query_params.get("barber_id", ["default_barber"])[0]

# --- Firebase References ---
walkin_ref = db.reference(f"barbers/{barber_id}/walkins")
booking_ref = db.reference(f"barbers/{barber_id}/bookings")
settings_ref = db.reference(f"barbers/{barber_id}/settings")

settings = settings_ref.get() or {}
avg_cut_duration = settings.get("avg_cut_duration", 25)
open_hour = settings.get("open_hour", 10)
close_hour = settings.get("close_hour", 22)
shop_name = settings.get("shop_name", "the barbershop")
logo_url = settings.get("logo_url")

# --- Page Setup ---
st.set_page_config(page_title="Book Appointment", layout="centered")

if logo_url:
    st.image(logo_url, width=180)

st.title(f"📅 Book with {shop_name}")

# --- Confirmation Banner ---
if "booking_confirmation" in st.session_state:
    booking = st.session_state["booking_confirmation"]
    dt = datetime.fromisoformat(booking["datetime"]).astimezone(ZoneInfo("Europe/London"))
    formatted_dt = dt.strftime("%A %d %B at %I:%M %p")
    st.success(f"✅ {booking['name']}, your booking is confirmed for {formatted_dt}.")

# --- Timezone & Date Setup ---
tz = ZoneInfo("Europe/London")
now = datetime.now(tz).replace(second=0, microsecond=0)
today = now.date()

st.subheader("🗓️ Select Date for Booking")
selected_date = st.date_input("Pick a date:", min_value=today)

# --- Continue if date selected ---
if selected_date:
    open_time = datetime.combine(selected_date, datetime.min.time(), tzinfo=tz).replace(hour=open_hour)
    close_time = datetime.combine(selected_date, datetime.min.time(), tzinfo=tz).replace(hour=close_hour)

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

    # Block walk-ins (only if date is today)
    if selected_date == today:
        walkin_queue = [
            datetime.fromisoformat(v["joined_at"]).replace(tzinfo=tz)
            for _, v in sorted_walkins
            if datetime.fromisoformat(v["joined_at"]).date() == today
        ]
        walkin_start = max(open_time, now)
        for _ in walkin_queue:
            blocked_slots.append((walkin_start, walkin_start + timedelta(minutes=avg_cut_duration)))
            walkin_start += timedelta(minutes=avg_cut_duration)

    # Block existing bookings
    for _, b in sorted_bookings:
        slot_dt = datetime.fromisoformat(b["slot"]).replace(tzinfo=tz)
        if slot_dt.date() == selected_date:
            blocked_slots.append((slot_dt, slot_dt + timedelta(minutes=avg_cut_duration)))

    # --- Calculate available slots ---
    available_slots = []
    slot = open_time
    while slot + timedelta(minutes=avg_cut_duration) <= close_time:
        if selected_date == today and slot < now:
            slot += timedelta(minutes=avg_cut_duration)
            continue

        overlap = any(
            bs <= slot < be or
            (slot <= bs < slot + timedelta(minutes=avg_cut_duration))
            for bs, be in blocked_slots
        )

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
