import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- Config ---
st.set_page_config(page_title="Barber Queue", layout="wide")
st_autorefresh(interval=20 * 1000, limit=None, key="auto_refresh")

# --- Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {
        'databaseURL': st.secrets["firebase_db_url"]
    })

walkin_ref = db.reference("walkins")
avg_cut_duration = 25  # default minutes per cut

# --- UI Toggles ---
# --- Secure Admin Login ---
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

is_kiosk = st.toggle("🖥️ Kiosk Display Mode")

if not is_kiosk and not st.session_state["is_admin"]:
    with st.expander("🔐 Admin Login"):
        entered_pin = st.text_input("Enter Admin PIN", type="password")
        if st.button("Login"):
            if entered_pin == st.secrets.get("admin_pin", "4321"):
                st.session_state["is_admin"] = True
                st.success("Admin access granted.")
                st.rerun()
            else:
                st.error("Incorrect PIN.")

# Set flag
is_admin = st.session_state["is_admin"] and not is_kiosk


st.title("💈 Live Barber Queue Tracker")

# --- Queue Add Form (Disabled in Admin/Kiosk Mode) ---
if not is_admin and not is_kiosk:
    with st.form("walkin_form"):
        name = st.text_input("Enter your name to join the queue:", placeholder="e.g. Ali")
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
st.subheader("📋 Current Queue")
walkins = walkin_ref.get()
now = datetime.now()

if walkins:
    sorted_walkins = sorted(walkins.items(), key=lambda x: x[1]["joined_at"])

    for i, (key, person) in enumerate(sorted_walkins):
        wait_mins = avg_cut_duration * i
        est_start = now + timedelta(minutes=wait_mins)
        est_end = est_start + timedelta(minutes=avg_cut_duration)

        # 🆕 Name logic (showing anonymised name unless admin
        display_name = person["name"] if is_admin else f"Person {i + 1}"

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"### {i + 1}. {display_name}  \n"
                f"🕒 Wait: {wait_mins} mins  \n"
                f"📅 Est: {est_start.strftime('%H:%M')} - {est_end.strftime('%H:%M')}"
            )
        with col2:
            if is_admin:
                if st.button("✅ Done", key=f"done_{key}", use_container_width=True):
                    walkin_ref.child(key).delete()
                    st.success(f"{person['name']} marked as done.")
                    st.rerun()
else:
    st.info("No one is in the queue yet.")