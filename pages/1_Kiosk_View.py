import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- Firebase init (singleton) ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {'databaseURL': st.secrets["firebase_db_url"]})

walkin_ref = db.reference("walkins")
avg_cut_duration = 25
now = datetime.now()

st.set_page_config(page_title="Kiosk View", layout="wide")
st_autorefresh(interval=20_000, limit=None, key="kiosk_refresh")

st.title("💈 Queue Tracker – Kiosk View")
st.info("Add your FULL NAME to join the queue. Names are hidden for privacy. Only the Barber can see for identification purposes")

# --- Retrieve current queue (with error fallback) ---
try:
    walkins = walkin_ref.get() or {}
    sorted_walkins = sorted(walkins.items(), key=lambda x: x[1]["joined_at"])
except Exception as e:
    walkins = {}
    sorted_walkins = []
    st.error("⚠️ Failed to connect to the queue. Please try again later.")
    st.stop()

# --- ✍️ Join the queue form ---
with st.form("add_name_form"):
    name = st.text_input("Enter your first name to join the queue:", placeholder="e.g. Ali")
    submit = st.form_submit_button("➕ Join Queue")

    if submit and name.strip():
        name_clean = name.strip().title()
        already_in_queue = any(p["name"] == name_clean for _, p in sorted_walkins)

        if already_in_queue:
            st.warning(f"⚠️ {name_clean}, you're already in the queue!")
        else:
            walkin_ref.push({
                "name": name_clean,
                "joined_at": now.isoformat()
            })
            position = len(sorted_walkins) + 1
            est_start = now + timedelta(minutes=avg_cut_duration * (position - 1))
            est_wait = avg_cut_duration * (position - 1)
            st.success(f"✅ Added! You're number {position} in the queue.\n"
                       f"⏳ Est. wait: {est_wait} mins\n"
                       f"🕒 Est. time: {est_start.strftime('%H:%M')}")
            st.rerun()

st.divider()
st.subheader("📋 Live Queue")

# --- Show current queue anonymously ---
if sorted_walkins:
    for i, (_, person) in enumerate(sorted_walkins):
        wait_mins = avg_cut_duration * i
        start = now + timedelta(minutes=wait_mins)
        end = start + timedelta(minutes=avg_cut_duration)
        st.markdown(
            f"### Person {i+1}  \n"
            f"🕒 Wait: {wait_mins} mins  \n"
            f"📅 Est: {start.strftime('%H:%M')} – {end.strftime('%H:%M')}"
        )
else:
    st.info("No one is in the queue yet.")