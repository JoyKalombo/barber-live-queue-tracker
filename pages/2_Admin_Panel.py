import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from io import StringIO

from utils.firebase_utils import get_barber_config
from utils.session import get_barber_id

# --- Page Config ---
st.set_page_config(page_title="Admin Panel", layout="wide")

# --- Init Firebase (once) ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {'databaseURL': st.secrets["firebase_db_url"]})

# --- Get barber_id from query string ---
query_params = st.query_params
barber_id = query_params.get("barber", "default_barber")

# --- Load barber config ---
config = get_barber_config(barber_id)

# --- Firebase Refs for this barber ---
walkin_ref = db.reference(f"barbers/{barber_id}/walkins")
booking_ref = db.reference(f"barbers/{barber_id}/bookings")
pin_ref = db.reference(f"barbers/{barber_id}/config/admin_pin")

avg_cut_duration = 25
now = datetime.now(ZoneInfo("Europe/London"))
open_time = now.replace(hour=10, minute=0, second=0, microsecond=0)

# --- PIN Login Check ---
st.title(f"🔐 Admin Panel – {barber_id.replace('_', ' ').title()}")

if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

stored_pin = pin_ref.get()

if not st.session_state["is_admin"]:
    entered_pin = st.text_input("Enter Admin PIN:", type="password")
    if st.button("Login"):
        if entered_pin == stored_pin:
            st.session_state["is_admin"] = True
            st.success("✅ Access granted.")
            st.rerun()
        else:
            st.error("❌ Incorrect PIN.")
    st.stop()

if st.button("🚪 Logout"):
    st.session_state["is_admin"] = False
    st.rerun()

# --- Queue Display ---
st.subheader("📋 Current Queue")

walkins = walkin_ref.get() or {}
bookings = booking_ref.get() or {}

# Sort both
sorted_walkins = sorted(walkins.items(), key=lambda x: x[1]["joined_at"])
sorted_bookings = sorted(bookings.items(), key=lambda x: x[1]["slot"])

queue = []
used_slots = []

# Add booking slots
for _, booking in sorted_bookings:
    try:
        start = datetime.fromisoformat(booking["slot"]).replace(tzinfo=ZoneInfo("Europe/London"))
        end = start + timedelta(minutes=avg_cut_duration)
        used_slots.append((start, end))
    except Exception:
        continue

# Assign walk-ins dynamically
walkin_time = max(now, open_time)
for _, walkin in sorted_walkins:
    while any(start <= walkin_time < end for start, end in used_slots):
        walkin_time += timedelta(minutes=avg_cut_duration)

    estimated_start = walkin_time
    estimated_end = estimated_start + timedelta(minutes=avg_cut_duration)
    used_slots.append((estimated_start, estimated_end))

    queue.append({
        "name": walkin["name"],
        "source": "walkin",
        "start": estimated_start
    })

    walkin_time = estimated_end

# Add bookings
for _, booking in sorted_bookings:
    try:
        start = datetime.fromisoformat(booking["slot"]).replace(tzinfo=ZoneInfo("Europe/London"))
        queue.append({
            "name": booking["name"],
            "source": "booking",
            "start": start
        })
    except Exception:
        continue

queue_sorted = sorted(queue, key=lambda x: x["start"])

# --- Display Queue ---
if queue_sorted:
    for i, person in enumerate(queue_sorted):
        wait_mins = int((person["start"] - now).total_seconds() / 60)
        end = person["start"] + timedelta(minutes=avg_cut_duration)

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"### {i+1}. {person['name']} ({person['source'].title()})\n"
                f"🕒 Wait: {max(0, wait_mins)} mins  \n"
                f"📅 Est: {person['start'].strftime('%H:%M')} – {end.strftime('%H:%M')}"
            )
        with col2:
            if st.button("✅ Done", key=f"remove_{i}"):
                ref_to_edit = walkin_ref if person["source"] == "walkin" else booking_ref
                entries = walkins if person["source"] == "walkin" else bookings

                for key, entry in entries.items():
                    if entry.get("name") == person["name"]:
                        if person["source"] == "booking":
                            if entry.get("slot") != person["start"].isoformat():
                                continue
                        ref_to_edit.child(key).delete()
                        break
                st.rerun()
else:
    st.info("No one is in the queue yet.")

# --- Export CSV ---
st.divider()
st.subheader("📁 Export Logs")

if st.button("⬇️ Export Today's Log as CSV"):
    try:
        date_today = now.strftime("%Y-%m-%d")
        log_ref = db.reference(f"logs/{date_today}")
        logs = log_ref.get()

        if logs:
            df = pd.DataFrame.from_dict(logs, orient="index")
            df["joined_at"] = pd.to_datetime(df["joined_at"])
            df = df.sort_values("joined_at")
            df["joined_at"] = df["joined_at"].dt.strftime("%Y-%m-%d %H:%M:%S")

            buffer = StringIO()
            df.to_csv(buffer, index=False)
            st.download_button(
                label="📥 Download CSV",
                data=buffer.getvalue(),
                file_name=f"queue_log_{barber_id}_{date_today}.csv",
                mime="text/csv"
            )
        else:
            st.info("ℹ️ No logs found for today.")
    except Exception as e:
        st.error(f"⚠️ Failed to export logs: {e}")