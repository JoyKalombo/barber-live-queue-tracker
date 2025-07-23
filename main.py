import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db

# --- Initialise Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {
        'databaseURL': st.secrets["firebase_db_url"]
    })

# --- Test DB Connection ---
ref = db.reference('test_connection')
ref.set({'message': 'Hello from Streamlit!'})

# --- Show success
st.success("✅ Firebase is connected and test message sent.")