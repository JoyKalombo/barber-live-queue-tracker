import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
from datetime import datetime

# Firebase init
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {'databaseURL': st.secrets["firebase_db_url"]})

st.set_page_config(page_title="Export Logs", layout="wide")
st.title("📥 Export Daily Queue Logs")

date_selected = st.date_input("Pick a date to export", value=datetime.today()).strftime("%Y-%m-%d")
log_ref = db.reference(f"logs/{date_selected}")
logs = log_ref.get()

if logs:
    df = pd.DataFrame(logs.values())
    df["joined_at"] = pd.to_datetime(df["joined_at"])
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", data=csv, file_name=f"{date_selected}_queue.csv", mime="text/csv")
else:
    st.info("No logs found for that date.")