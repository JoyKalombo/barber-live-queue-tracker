import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# --- Initialise Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {
        'databaseURL': st.secrets["firebase_db_url"]
    })

# --- Firebase DB Reference ---
walkin_ref = db.reference('walkins')

st.title("💈 Live Barber Queue Tracker")

# --- Add to Queue ---
with st.form("walkin_form"):
    name = st.text_input("Enter your name to join the queue:")
    submit = st.form_submit_button("Join Queue")

    if submit and name:
        timestamp = datetime.now().isoformat()
        walkin_ref.push({
            "name": name,
            "joined_at": timestamp
        })
        st.success(f"You're in the queue, {name}!")

st.divider()

# --- Show Current Walk-in Queue ---
st.subheader("📋 Current Walk-ins")
walkins = walkin_ref.get()

if walkins:
    sorted_walkins = sorted(walkins.items(), key=lambda x: x[1]["joined_at"])
    for i, (_, person) in enumerate(sorted_walkins, 1):
        st.write(f"{i}. {person['name']} (joined at {person['joined_at'][11:16]})")
else:
    st.info("No one in the queue yet.")