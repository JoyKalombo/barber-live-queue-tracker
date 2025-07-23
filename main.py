import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="Barber Queue", layout="wide")

# --- Initialise Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {
        'databaseURL': st.secrets["firebase_db_url"]
    })

walkin_ref = db.reference('walkins')

st.title("💈 Live Barber Queue Tracker")

# --- Admin Mode Toggle ---
is_admin = st.checkbox("🔐 Barber/Admin Mode")

# --- Walk-in Form (hidden in admin mode) ---
if not is_admin:
    with st.form("walkin_form"):
        name = st.text_input("Enter your name to join the queue:", placeholder="e.g. Ali", label_visibility="visible")
        submit = st.form_submit_button("➕ Join Queue")

        if submit and name.strip():
            walkin_ref.push({
                "name": name.strip().title(),
                "joined_at": datetime.now().isoformat()
            })
            st.success(f"You're in the queue, {name.strip().title()}!")
            st.rerun()

st.divider()

# --- Queue Display ---
st.subheader("📋 Current Walk-ins")

walkins = walkin_ref.get()

if walkins:
    sorted_walkins = sorted(walkins.items(), key=lambda x: x[1]["joined_at"])

    for i, (key, person) in enumerate(sorted_walkins, 1):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"### {i}. {person['name']} &nbsp;&nbsp;🕒 {person['joined_at'][11:16]}")
        with col2:
            if is_admin:
                if st.button("✅ Done", key=f"done_{key}", use_container_width=True):
                    walkin_ref.child(key).delete()
                    st.success(f"{person['name']} marked as done.")
                    st.experimental_rerun()
else:
    st.info("No one is in the queue yet.")