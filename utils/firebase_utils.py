# utils/firebase_utils.py
import firebase_admin
from firebase_admin import credentials, db
import json
import streamlit as st

# Initialise Firebase if not already done
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {
        'databaseURL': st.secrets["firebase_db_url"]
    })


def get_barber_config(barber_id: str = "default_barber") -> dict:
    ref = db.reference(f"barbers/{barber_id}/settings")
    return ref.get() or {}


def get_all_barber_ids() -> list:
    ref = db.reference("barbers")
    return list(ref.get().keys()) if ref.get() else []
