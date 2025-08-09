# utils/firebase_utils.py
import firebase_admin
from firebase_admin import credentials, db
import json
import streamlit as st
import re
from datetime import datetime

# Initialise Firebase if not already done
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {
        'databaseURL': st.secrets["firebase_db_url"]
    })


def get_barber_config(barber_id: str = "default_barber") -> dict:
    ref = db.reference(f"barbers/{barber_id}/settings")
    config = ref.get() or {}
    st.write(f"DEBUG: Fetched barber config for {barber_id}: {config}")  # Debugging line
    return config


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


def is_valid_uk_phone(phone):
    """Check if phone is a valid UK mobile number (e.g. 07912345678)"""
    return re.fullmatch(r"07\d{9}", phone) is not None


def push_booking(barber_id, name, phone, slot_datetime):
    """
    Pushes a new booking to Firebase under the given barber's node.
    Validates UK phone format before pushing.
    """
    if not is_valid_uk_phone(phone):
        raise ValueError("Invalid phone number. Must start with '07' and be 11 digits.")

    slot_str = slot_datetime.isoformat()
    booking_data = {
        "name": name.strip(),
        "phone": phone.strip(),
        "slot": slot_str
    }

    db.reference(f"barbers/{barber_id}/bookings").push(booking_data)
