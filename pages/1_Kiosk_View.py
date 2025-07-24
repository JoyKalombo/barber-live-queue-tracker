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

# --- Auto-refresh every 20s ---
st_autorefresh(interval=20_000, limit=None, key="kiosk_refresh")

st.title("💈 Queue Tracker – Kiosk View")
st.info("Add your name and see estimated wait time. Names are hidden for privacy.")

# --- ✍️ Join the queue form ---
with st.form("add_name_form"):
    name = st.text_input("Enter your first name to join the queue:", placeholder="e.g. Ali")
    submit = st.form_submit_button("➕ Join Queue")
    if submit and name.strip():
        walkin_ref.push({
            "name": name.strip().title(),
            "joined_at": now.isoformat()
        })
        st.success("✅ You've been added to the queue!")
        st.rerun()

st.divider()
st.subheader("📋 Live Queue (Anonymised)")

# --- Queue display ---
walkins = walkin_ref.get()
if walkins:
    sorted_walkins = sorted(walkins.items(), key=lambda x: x[1]["joined_at"])
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