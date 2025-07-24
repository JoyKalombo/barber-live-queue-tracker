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

# --- Show confirmation if in session ---
if "confirmation_message" in st.session_state:
    m = st.session_state["confirmation_message"]
    st.success(
        f"✅ {m['name']}, you've been added to the queue!\n\n"
        f"You're number **{m['position']}** in line.\n\n"
        f"⏳ Est. wait: **{m['wait']} mins**\n\n"
        f"🕒 Est. time: **{m['time']}**"
    )
    # Only run one refresh with a separate key
    if st_autorefresh(interval=20_000, limit=1, key="clear_confirmation_refresh"):
        del st.session_state["confirmation_message"]
else:
    # Standard recurring refresh
    st_autorefresh(interval=20_000, limit=None, key="regular_kiosk_refresh")

st.info("Add your FULL NAME to join the queue. Names are hidden for privacy. Only the Barber can see your name.")

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
            # Push to main walk-ins list
            walkin_ref.push({
                "name": name_clean,
                "joined_at": now.isoformat()
            })

            # Also log to date-based logs
            date_today = datetime.now().strftime("%Y-%m-%d")
            log_ref = db.reference(f"logs/{date_today}")
            log_ref.push({
                "name": name_clean,
                "joined_at": now.isoformat()
            })

            position = len(sorted_walkins) + 1
            est_start = now + timedelta(minutes=avg_cut_duration * (position - 1))
            est_wait = avg_cut_duration * (position - 1)

            # Store confirmation in session_state
            st.session_state["confirmation_message"] = {
                "name": name_clean,
                "position": position,
                "wait": est_wait,
                "time": est_start.strftime('%H:%M')
            }

            st.experimental_set_query_params(added="1")  # dummy param to avoid refresh loop
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