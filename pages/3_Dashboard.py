import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# --- Firebase init ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {'databaseURL': st.secrets["firebase_db_url"]})

walkin_ref = db.reference("walkins")
st.set_page_config(page_title="Barber Dashboard", layout="wide")
st.title("📊 Barber Dashboard")

walkins = walkin_ref.get()

if not walkins:
    st.info("No walk-ins yet today.")
    st.stop()

sorted_walkins = sorted(walkins.items(), key=lambda x: x[1]["joined_at"])
now = datetime.now()

# --- Dashboard Stats ---
st.subheader("📈 Key Stats")

total_in_queue = len(sorted_walkins)
estimated_total_wait = total_in_queue * 25  # You can refine this later

st.metric(label="👥 People in Queue", value=total_in_queue)
st.metric(label="⏳ Estimated Total Wait", value=f"{estimated_total_wait} mins")

first_joined = datetime.fromisoformat(sorted_walkins[0][1]["joined_at"])
wait_so_far = (now - first_joined).seconds // 60

st.metric(label="🕒 Oldest Wait Time", value=f"{wait_so_far} mins")

# Optional chart placeholder
st.divider()
st.subheader("📅 Timeline Preview (Coming Soon)")
st.info("Charts and trends will go here.")