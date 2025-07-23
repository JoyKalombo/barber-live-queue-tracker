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

# --- Admin Mode Toggle ---
is_admin = st.checkbox("🔐 Barber/Admin Mode")

# --- Add to Queue (Only if not Admin) ---
if not is_admin:
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
    for i, (key, person) in enumerate(sorted_walkins, 1):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"{i}. {person['name']} (joined at {person['joined_at'][11:16]})")
        with col2:
            if is_admin:
                if st.button("✅ Done", key=f"done_{key}"):
                    walkin_ref.child(key).delete()
                    st.success(f"{person['name']} marked as done.")
                    st.experimental_rerun()
else:
    st.info("No one in the queue yet.")
