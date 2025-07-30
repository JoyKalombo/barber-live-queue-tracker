import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh
from utils.firebase_utils import get_barber_config
from utils.session import get_barber_id

# ✅ MAKING BARBER SPECIFIC REQESUTS
barber_id = get_barber_id()
config = get_barber_config(barber_id)

# ✅ Submit name to barber-specific queue
name = st.text_input("Enter your name:")
if st.button("Join Queue"):
    db.reference(f"barbers/{barber_id}/queue").push({"name": name})
    queue_ref = db.reference(f"barbers/{barber_id}/queue")
    queue_ref.push({"name": name})
    st.success(f"{name}, you're in the queue for {barber_id.replace('_', ' ').title()}!")

# ✅ Show barber-specific queue
queue_ref = db.reference(f"barbers/{barber_id}/queue")
queue_data = queue_ref.get() or {}
st.write("Current Queue:")
for entry in queue_data.values():
    st.write(f"• {entry['name']}")

st.title(f" 💈 Kiosk for {barber_id.replace('_', ' ').title()}")


# --- Handle barber ID from URL ---
query_params = st.query_params
barber_id = query_params.get("barber", "default_barber")

# Load the barber config
config = get_barber_config(barber_id)

# --- Firebase init (singleton) ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {'databaseURL': st.secrets["firebase_db_url"]})

walkin_ref = db.reference("walkins")
booking_ref = db.reference("bookings")
avg_cut_duration = 25
open_time = datetime.now(ZoneInfo("Europe/London")).replace(hour=10, minute=0, second=0, microsecond=0)
now = datetime.now(ZoneInfo("Europe/London"))

st.set_page_config(page_title="Kiosk View", layout="wide")
st.title("💈 Queue Tracker – Kiosk View")
st_autorefresh(interval=20_000, limit=None, key="kiosk_refresh")

# --- Show confirmation if in session ---
if "confirmation_message" in st.session_state:
    m = st.session_state["confirmation_message"]
    st.success(
        f"✅ {m['name']}, you've been added to the queue!\n\n"
        f"You're number **{m['position']}** in line.\n\n"
        f"⏳ Est. wait: **{m['wait']} mins**\n\n"
        f"🕒 Est. time: **{m['time']}**"
    )
    if st_autorefresh(interval=20_000, limit=1, key="clear_confirmation_refresh"):
        del st.session_state["confirmation_message"]

st.info("Add your FULL NAME to join the queue. Names are hidden for privacy. Only the Barber can see your name.")

# --- Retrieve queue data ---
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

    # Create unified queue
    queue = []

    # --- Calculate walk-in slots dynamically ---
    used_slots = []

    # Add booking slots to the list of used time windows
    for _, booking in sorted_bookings:
        start = datetime.fromisoformat(booking["slot"]).replace(tzinfo=ZoneInfo("Europe/London"))
        end = start + timedelta(minutes=avg_cut_duration)
        used_slots.append((start, end))

    # Start from the later of 'now' or 'open_time'
    walkin_time = max(now, open_time)

    for _, walkin in sorted_walkins:
        # Find next available time that doesn't conflict
        while any(start <= walkin_time < end for start, end in used_slots):
            walkin_time += timedelta(minutes=avg_cut_duration)

        estimated_start = walkin_time
        estimated_end = estimated_start + timedelta(minutes=avg_cut_duration)
        used_slots.append((estimated_start, estimated_end))  # block it for the next one

        queue.append({
            "source": "walkin",
            "start": estimated_start
        })

        walkin_time = estimated_end  # next possible start time

    # Add bookings with their slot times
    for _, person in sorted_bookings:
        queue.append({
            "source": "booking",
            "start": datetime.fromisoformat(booking["slot"]).replace(tzinfo=ZoneInfo("Europe/London"))
        })

    # Sort final queue
    queue_sorted = sorted(queue, key=lambda x: x["start"])

except Exception as e:
    st.error("⚠️ Failed to load queue data. Please try again later.")
    st.exception(e)  # 👈 shows what actually went wrong
    st.stop()

# --- Join the queue form ---
with st.form("add_name_form"):
    name = st.text_input("Enter your full name to join the queue:", placeholder="e.g. Ali")
    submit = st.form_submit_button("➕ Join Queue")

    if submit and name.strip():
        name_clean = name.strip().title()
        already_in_queue = any(
            p.get("name", "") == name_clean for _, p in sorted_walkins
        )

        if already_in_queue:
            st.warning(f"⚠️ {name_clean}, you're already in the queue!")
        else:
            walkin_ref.push({
                "name": name_clean,
                "joined_at": now.isoformat()
            })

            # Also log
            date_today = now.strftime("%Y-%m-%d")
            log_ref = db.reference(f"logs/{date_today}")
            log_ref.push({
                "name": name_clean,
                "joined_at": now.isoformat()
            })

            # Recalculate used slots
            all_used = []

            for _, b in sorted_bookings:
                start = datetime.fromisoformat(b["slot"])
                if start.tzinfo is None:
                    start = start.replace(tzinfo=ZoneInfo("Europe/London"))
                end = start + timedelta(minutes=avg_cut_duration)
                all_used.append((start, end))

            # Rebuild walk-in slots like we do in the main queue
            walkin_time = max(now, open_time)

            # Block future walk-ins by recalculating their actual allocated slots
            for _, w in sorted_walkins:
                # Skip walk-ins that were joined before today or long ago (optional, based on your needs)
                joined_at = datetime.fromisoformat(w["joined_at"])
                if joined_at.tzinfo is None:
                    joined_at = joined_at.replace(tzinfo=ZoneInfo("Europe/London"))

                if joined_at.date() != now.date():
                    continue  # skip old entries

                all_used = [
                    (start, end)
                    for start, end in all_used
                    if isinstance(start, datetime) and isinstance(end, datetime)
                ]

                while any(start <= walkin_time < end for start, end in all_used):
                    walkin_time += timedelta(minutes=avg_cut_duration)

                if walkin_time < now:
                    # Skip this walk-in because their slot would have been in the past
                    walkin_time += timedelta(minutes=avg_cut_duration)
                    continue

                est_start = walkin_time
                est_end = est_start + timedelta(minutes=avg_cut_duration)
                all_used.append((est_start, est_end))
                walkin_time = est_end

            # Find next valid walk-in slot
            candidate_time = max(now, open_time)
            while any(start <= candidate_time < end for start, end in all_used):
                candidate_time += timedelta(minutes=avg_cut_duration)

            # Add to confirmation message
            est_start = candidate_time
            est_wait = int((est_start - now).total_seconds() / 60)

            st.session_state["confirmation_message"] = {
                "name": name_clean,
                "position": len(queue_sorted) + 1,
                "wait": est_wait,
                "time": est_start.strftime('%H:%M')
            }

            st.experimental_set_query_params(added="1")
            st.rerun()

# --- Display Live Queue ---
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