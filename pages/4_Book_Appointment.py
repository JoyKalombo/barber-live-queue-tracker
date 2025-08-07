import streamlit as st
import json
import re
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh

from utils.firebase_utils import get_barber_config
from utils.session import get_barber_id

# --- Helpers ---
UK_MOBILE_RE = re.compile(r"^07\d{9}$")

def is_valid_uk_mobile(phone: str) -> bool:
    return bool(UK_MOBILE_RE.fullmatch(phone.strip()))

def to_e164_uk(phone: str) -> str:
    """Convert 07xxxxxxxxx -> +447xxxxxxxxx (simple UK-only normalizer)."""
    p = phone.strip().replace(" ", "")
    if p.startswith("+44"):
        return p
    if p.startswith("07") and len(p) == 11:
        return "+44" + p[1:]
    return p  # fallback (won't pass validation if wrong)

# --- Handle barber ID from URL ---
query_params = st.query_params
barber_id = query_params.get("barber", "default_barber")
st.info(f"Barber ID: {barber_id}")

# --- Firebase init ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {'databaseURL': st.secrets["firebase_db_url"]})

# Load the barber config
config = get_barber_config(barber_id)

# Firebase References (barber-specific)
walkin_ref = db.reference(f"barbers/{barber_id}/walkins")
booking_ref = db.reference(f"barbers/{barber_id}/bookings")
settings_ref = db.reference(f"barbers/{barber_id}/settings")

# --- Page Setup ---
st.set_page_config(page_title="Book Appointment", layout="centered")
settings = settings_ref.get() or {}
avg_cut_duration = int(settings.get("avg_cut_duration", 25))
open_hour = int(settings.get("open_hour", 10))
close_hour = int(settings.get("close_hour", 22))
shop_name = settings.get("shop_name", "the barbershop")
logo_url = settings.get("logo_url")

if logo_url:
    st.image(logo_url, width=180)

st.title(f"📅 Book with {shop_name}")

# --- Confirmation Banner ---
if "booking_confirmation" in st.session_state:
    booking = st.session_state["booking_confirmation"]
    dt = datetime.fromisoformat(booking["datetime"]).astimezone(ZoneInfo("Europe/London"))
    formatted_dt = dt.strftime("%A %d %B at %I:%M %p")
    st.success(f"✅ {booking['name']}, your booking is confirmed for {formatted_dt}.")

# --- Timezone & Date Setup ---
tz = ZoneInfo("Europe/London")
now = datetime.now(tz).replace(second=0, microsecond=0)
today = now.date()

st.subheader("🗓️ Select Date for Booking")
selected_date = st.date_input("Pick a date:", min_value=today)

# --- Continue if date selected ---
if selected_date:
    open_time = datetime.combine(selected_date, datetime.min.time(), tzinfo=tz).replace(hour=open_hour)
    close_time = datetime.combine(selected_date, datetime.min.time(), tzinfo=tz).replace(hour=close_hour)

    walkins = walkin_ref.get() or {}
    bookings = booking_ref.get() or {}

    sorted_walkins = sorted(
        [(k, v) for k, v in walkins.items() if "joined_at" in v],
        key=lambda x: x[1]["joined_at"]
    )
    sorted_bookings = sorted(
        [(k, v) for k, v in bookings.items() if "slot" in v],
        key=lambda x: x[1]["slot"]
    )

    # --- Generate blocked time ranges ---
    blocked_slots = []

    # Block walk-ins (only if date is today)
    if selected_date == today:
        walkin_queue = [
            datetime.fromisoformat(v["joined_at"]).replace(tzinfo=tz)
            for _, v in sorted_walkins
            if "joined_at" in v and datetime.fromisoformat(v["joined_at"]).date() == today
        ]
        walkin_start = max(open_time, now)
        for _ in walkin_queue:
            blocked_slots.append((walkin_start, walkin_start + timedelta(minutes=avg_cut_duration)))
            walkin_start += timedelta(minutes=avg_cut_duration)

    # Block existing bookings
    for _, b in sorted_bookings:
        try:
            slot_dt = datetime.fromisoformat(b["slot"])
            if slot_dt.tzinfo is None:
                slot_dt = slot_dt.replace(tzinfo=tz)
        except Exception:
            continue
        if slot_dt.date() == selected_date:
            blocked_slots.append((slot_dt, slot_dt + timedelta(minutes=avg_cut_duration)))

    # --- Calculate available slots ---
    available_slots = []
    slot = open_time
    while slot + timedelta(minutes=avg_cut_duration) <= close_time:
        if selected_date == today and slot < now:
            slot += timedelta(minutes=avg_cut_duration)
            continue

        overlap = any(
            (bs <= slot < be) or (slot <= bs < slot + timedelta(minutes=avg_cut_duration))
            for bs, be in blocked_slots
        )

        if not overlap:
            available_slots.append(slot)

        slot += timedelta(minutes=avg_cut_duration)

    # --- Booking Form ---
    if available_slots:
        with st.form("booking_form"):
            name = st.text_input("Enter your full name:")
            phone = st.text_input("Mobile number (UK, e.g. 07123456789)")
            chosen_slot_label = st.selectbox(
                "Pick an available time:",
                [s.strftime('%H:%M') for s in available_slots]
            )
            submitted = st.form_submit_button("📥 Confirm Booking")

        # Live hints (outside submit)
        if phone and not is_valid_uk_mobile(phone):
            st.warning("Phone must start with **07** and be **11 digits**.")

        if submitted:
            errors = []
            if not name.strip():
                errors.append("Please enter your name.")
            if not is_valid_uk_mobile(phone):
                errors.append("Invalid UK mobile number. Use 07123456789 format.")
            try:
                selected_time = next(s for s in available_slots if s.strftime('%H:%M') == chosen_slot_label)
            except StopIteration:
                errors.append("Selected slot is no longer available. Please refresh and try again.")

            # Duplicate booking check: same phone + slot
            if not errors:
                slot_iso = selected_time.isoformat()
                existing = booking_ref.get() or {}
                duplicate = False
                for _, rec in (existing.items() if isinstance(existing, dict) else []):
                    if rec.get("slot") == slot_iso and rec.get("phone_e164") == to_e164_uk(phone):
                        duplicate = True
                        break
                if duplicate:
                    errors.append("You already have a booking for this time with this phone number.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                # Save to Firebase
                booking_ref.push({
                    "name": name.strip().title(),
                    "phone_local": phone.strip(),
                    "phone_e164": to_e164_uk(phone),
                    "slot": selected_time.isoformat(),           # tz-aware ISO8601
                    "created_at": now.isoformat(),               # tz-aware
                    "status": "confirmed",
                    "source": "self_service",
                })

                st.session_state["booking_confirmation"] = {
                    "name": name.strip().title(),
                    "datetime": selected_time.isoformat()
                }
                st.rerun()
    else:
        st.info("🕒 No appointment slots available for this date.")