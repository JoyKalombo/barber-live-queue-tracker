import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from io import StringIO

# --- Firebase init ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {'databaseURL': st.secrets["firebase_db_url"]})

walkin_ref = db.reference("walkins")
booking_ref = db.reference("bookings")
avg_cut_duration = 25  # in minutes
now = datetime.now(ZoneInfo("Europe/London"))
open_time = datetime.now(ZoneInfo("Europe/London")).replace(hour=10, minute=0, second=0, microsecond=0)

st.set_page_config(page_title="Admin Panel", layout="wide")

# --- Session state login ---
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

if not st.session_state["is_admin"]:
    st.title("🔐 Admin Login")
    entered_pin = st.text_input("Enter Admin PIN:", type="password")
    if st.button("Login"):
        if entered_pin == st.secrets.get("admin_pin", "4321"):
            st.session_state["is_admin"] = True
            st.rerun()
        else:
            st.error("❌ Incorrect PIN.")
    st.stop()

# --- Admin interface ---
st.title("💈 Barber Admin Panel")

if st.button("🚪 Logout"):
    st.session_state["is_admin"] = False
    st.rerun()

# --- Pull from Firebase ---
walkins = walkin_ref.get() or {}
bookings = booking_ref.get() or {}

# --- Sort both ---
sorted_walkins = sorted(walkins.items(), key=lambda x: x[1]["joined_at"])
sorted_bookings = sorted(bookings.items(), key=lambda x: x[1]["slot"])

# --- Create unified queue list with estimated start times ---
queue = []

# Add walk-ins with calculated time
used_slots = []

# Add booking time slots to used list
for _, booking in sorted_bookings:
    start = datetime.fromisoformat(booking["slot"])
    end = start + timedelta(minutes=avg_cut_duration)
    used_slots.append((start, end))

# Dynamically assign walk-in slots avoiding clashes
walkin_time = max(now, open_time)

for _, walkin in sorted_walkins:
    # Find the next time that doesn’t clash
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

    walkin_time = estimated_end  # move forward


# Add bookings with actual slot time
for _, person in sorted_bookings:
    queue.append({
        "name": person["name"],
        "source": "booking",
        "start": datetime.fromisoformat(person["slot"])
    })

# --- Sort unified queue by start time ---
queue_sorted = sorted(queue, key=lambda x: x["start"])

# --- Queue Display ---
st.subheader("🧑‍🦱 Queue Overview (Walk-ins + Bookings)")

if queue_sorted:
    for i, person in enumerate(queue_sorted):
        wait_mins = int((person["start"] - now).total_seconds() / 60)
        end_time = person["start"] + timedelta(minutes=avg_cut_duration)

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"### {i+1}. {person['name']} ({'Booking' if person['source'] == 'booking' else 'Walk-in'})  \n"
                f"🕒 Wait: {max(wait_mins, 0)} mins  \n"
                f"📅 Est: {person['start'].strftime('%H:%M')} – {end_time.strftime('%H:%M')}"
            )
        with col2:
            if st.button("✅ Done", key=f"remove_{i}"):
                # Remove from appropriate Firebase reference
                if person["source"] == "walkin":
                    # Find and delete walk-in
                    for key, p in walkins.items():
                        if p["name"] == person["name"]:
                            walkin_ref.child(key).delete()
                            break
                else:
                    # Find and delete booking
                    for key, p in bookings.items():
                        if p["name"] == person["name"] and p["slot"] == person["start"].isoformat():
                            booking_ref.child(key).delete()
                            break
                st.rerun()

else:
    st.info("No one is in the queue yet.")

# --- CSV Export Section ---
st.divider()
st.subheader("📁 Export Logs")

if st.button("⬇️ Export Today's Log as CSV"):
    try:
        date_today = datetime.now().strftime("%Y-%m-%d")
        log_ref = db.reference(f"logs/{date_today}")
        logs = log_ref.get()

        if logs:
            df_logs = pd.DataFrame.from_dict(logs, orient="index")
            df_logs["joined_at"] = pd.to_datetime(df_logs["joined_at"])
            df_logs = df_logs.sort_values("joined_at")
            df_logs["joined_at"] = df_logs["joined_at"].dt.strftime("%Y-%m-%d %H:%M:%S")

            csv_buffer = StringIO()
            df_logs.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_buffer.getvalue(),
                file_name=f"queue_log_{date_today}.csv",
                mime="text/csv"
            )
        else:
            st.info("ℹ️ No logs found for today.")
    except Exception as e:
        st.error(f"⚠️ Failed to export logs: {str(e)}")