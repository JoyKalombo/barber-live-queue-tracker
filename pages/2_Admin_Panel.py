import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from io import StringIO

# --- Firebase init ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {'databaseURL': st.secrets["firebase_db_url"]})

walkin_ref = db.reference("walkins")
avg_cut_duration = 25
now = datetime.now()
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

# --- Queue Display & Remove Logic ---
walkins = walkin_ref.get()
if walkins:
    sorted_walkins = sorted(walkins.items(), key=lambda x: x[1]["joined_at"])
    for i, (key, person) in enumerate(sorted_walkins):
        wait_mins = avg_cut_duration * i
        start = now + timedelta(minutes=wait_mins)
        end = start + timedelta(minutes=avg_cut_duration)

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"### {i+1}. {person['name']}  \n"
                f"🕒 Wait: {wait_mins} mins  \n"
                f"📅 Est: {start.strftime('%H:%M')} – {end.strftime('%H:%M')}"
            )
        with col2:
            if st.button("✅ Done", key=f"done_{key}", use_container_width=True):
                walkin_ref.child(key).delete()
                st.success(f"{person['name']} removed from queue.")
                st.rerun()
else:
    st.info("No one is in the queue yet.")

# --- CSV Export Section (admin-only) ---
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