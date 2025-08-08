import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh
from utils.firebase_utils import get_barber_config
from utils.session import get_barber_id


# --- Page config ---
st.set_page_config(page_title="Kiosk View", layout="wide")

# --- Get barber ID from query params ---
query_params = st.query_params
barber_id = get_barber_id()
config = get_barber_config(barber_id)
st.info(f"Barber ID: {barber_id}")

# --- Firebase init (singleton) ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {'databaseURL': st.secrets["firebase_db_url"]})

# --- Refs for current barber ---
walkin_ref = db.reference(f"barbers/{barber_id}/walkins")
booking_ref = db.reference(f"barbers/{barber_id}/bookings")

# --- Constants ---
avg_cut_duration = 25
open_time = datetime.now(ZoneInfo("Europe/London")).replace(hour=10, minute=0, second=0, microsecond=0)
now = datetime.now(ZoneInfo("Europe/London"))

# --- Titles ---
st.title(f"💈 Queue Tracker – {barber_id.replace('_', ' ').title()} Kiosk")
st_autorefresh(interval=20_000, limit=None, key="kiosk_refresh")

# --- Confirmation Message ---
if "confirmation_message" in st.session_state:
    m = st.session_state["confirmation_message"]
    st.success(
        f"✅ {m['name']}, you're in line!\n\n"
        f"You're number **{m['position']}**.\n"
        f"⏳ Wait: **{m['wait']} mins**\n"
        f"🕒 Est. start: **{m['time']}**"
    )
    if st_autorefresh(interval=20_000, limit=1, key="clear_confirmation_refresh"):
        del st.session_state["confirmation_message"]

# --- User Prompt ---
st.info("Enter your full name to join the queue. Names are hidden for privacy.")

# --- Queue Data ---
try:
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

    # --- Time slot building ---
    queue = []
    used_slots = []

    for _, booking in sorted_bookings:
        start = datetime.fromisoformat(booking["slot"]).replace(tzinfo=ZoneInfo("Europe/London"))
        end = start + timedelta(minutes=avg_cut_duration)
        used_slots.append((start, end))

    walkin_time = max(now, open_time)
    for _, walkin in sorted_walkins:
        while any(start <= walkin_time < end for start, end in used_slots):
            walkin_time += timedelta(minutes=avg_cut_duration)

        estimated_start = walkin_time
        estimated_end = estimated_start + timedelta(minutes=avg_cut_duration)
        used_slots.append((estimated_start, estimated_end))
        queue.append({"source": "walkin", "start": estimated_start})
        walkin_time = estimated_end

    for _, person in sorted_bookings:
        queue.append({
            "source": "booking",
            "start": datetime.fromisoformat(person["slot"]).replace(tzinfo=ZoneInfo("Europe/London"))
        })

    queue_sorted = sorted(queue, key=lambda x: x["start"])

except Exception as e:
    st.error("⚠️ Failed to load queue data.")
    st.exception(e)
    st.stop()

# --- Form ---
with st.form("add_name_form"):
    name = st.text_input("Enter your full name:", placeholder="e.g. Ali")
    submit = st.form_submit_button("➕ Join Queue")

    if submit and name.strip():
        name_clean = name.strip().title()
        already_in_queue = any(p.get("name", "") == name_clean for _, p in sorted_walkins)

        if already_in_queue:
            st.warning(f"⚠️ {name_clean}, you're already in the queue!")
        else:
            now_iso = now.isoformat()
            walkin_ref.push({"name": name_clean, "joined_at": now_iso})
            db.reference(f"barbers/{barber_id}/logs/{now.strftime('%Y-%m-%d')}").push({
                "name": name_clean,
                "joined_at": now_iso
            })

            # Slot Calculation
            all_used = [
                (datetime.fromisoformat(b["slot"]).replace(tzinfo=ZoneInfo("Europe/London")),
                 datetime.fromisoformat(b["slot"]).replace(tzinfo=ZoneInfo("Europe/London")) + timedelta(minutes=avg_cut_duration))
                for _, b in sorted_bookings
            ]

            walkin_time = max(now, open_time)
            while any(start <= walkin_time < end for start, end in all_used):
                walkin_time += timedelta(minutes=avg_cut_duration)

            est_start = walkin_time
            est_wait = int((est_start - now).total_seconds() / 60)

            st.session_state["confirmation_message"] = {
                "name": name_clean,
                "position": len(queue_sorted) + 1,
                "wait": est_wait,
                "time": est_start.strftime('%H:%M')
            }

            st.experimental_set_query_params(added="1", barber=barber_id)
            st.rerun()

# --- Live Queue ---
st.divider()
st.subheader("📋 Live Queue")

if queue_sorted:
    for i, person in enumerate(queue_sorted):
        wait_mins = max(0, int((person["start"] - now).total_seconds() / 60))
        end = person["start"] + timedelta(minutes=avg_cut_duration)

        st.markdown(
            f"### Person {i + 1} ({'Booking' if person['source'] == 'booking' else 'Walk-in'})  \n"
            f"🕒 Wait: {wait_mins} mins  \n"
            f"📅 Est: {person['start'].strftime('%H:%M')} – {end.strftime('%H:%M')}"
        )
else:
    st.info("No one is currently in the queue.")