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


from firebase_admin import db
from datetime import datetime


def create_new_barber(barber_id: str):
    barber_ref = db.reference(f"barbers/{barber_id}")

    # 🔒 Safety check: Don't overwrite if already exists
    if barber_ref.get():
        print(f"❌ Barber '{barber_id}' already exists. Skipping creation.")
        return False

    # ✅ Default values
    barber_ref.set({
        "config": {
            "admin_pin": "0000"  # Change this manually or allow setting it dynamically
        },
        "settings": {
            "avg_cut_duration": 25,
            "open_hour": 10,
            "close_hour": 22,
            "shop_name": "New Barber",
            "logo_url": ""  # Optional: Set default logo
        },
        "walkins": {},
        "bookings": {},
        "logs": {
            datetime.now().strftime("%Y-%m-%d"): {}
        }
    })

    print(f"✅ Barber '{barber_id}' created successfully.")
    return True
