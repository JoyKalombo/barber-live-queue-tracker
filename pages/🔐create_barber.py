import streamlit as st
from firebase_admin import db

st.set_page_config(page_title="Create New Barber", layout="centered")
st.title("🔐 Super Admin – Add New Barber")

# --- Super Admin Access ---
SUPER_ADMIN_PIN = st.secrets.get("super_admin_pin", "9999")

if "super_admin_granted" not in st.session_state:
    st.session_state["super_admin_granted"] = False

if not st.session_state["super_admin_granted"]:
    entered_pin = st.text_input("Enter Super Admin PIN", type="password")
    if st.button("Unlock"):
        if entered_pin == SUPER_ADMIN_PIN:
            st.session_state["super_admin_granted"] = True
            st.success("✅ Access granted.")
            st.rerun()
        else:
            st.error("❌ Incorrect PIN.")
    st.stop()

# --- Create New Barber Form ---
st.subheader("✂️ Add a New Barber Shop")

with st.form("create_barber_form"):
    barber_id = st.text_input("🆔 Unique Barber ID", help="e.g. fade_culture_london")
    shop_name = st.text_input("🏪 Shop Name", help="e.g. Fade Culture")

    col1, col2 = st.columns(2)
    with col1:
        admin_pin = st.text_input("🔐 Admin PIN", type="password", key="pin_hidden")
    with col2:
        show_pin = st.checkbox("👁 Show PIN")
        if show_pin:
            admin_pin = st.text_input("🔐 Admin PIN (Visible)", key="pin_visible")

    logo_url = st.text_input("🖼️ Logo URL (optional)", help="Leave blank to auto-generate")
    avg_duration = st.number_input("✂️ Avg Cut Duration (mins)", value=25, min_value=10, max_value=120)
    open_hour = st.number_input("🕙 Open Hour (24hr)", value=10, min_value=0, max_value=23)
    close_hour = st.number_input("🕘 Close Hour (24hr)", value=22, min_value=0, max_value=23)

    submitted = st.form_submit_button("➕ Create Barber")

if submitted:
    if not barber_id.strip():
        st.error("❌ Barber ID is required.")
    else:
        barber_ref = db.reference(f"barbers/{barber_id}")
        if barber_ref.get():
            st.warning(f"⚠️ Barber '{barber_id}' already exists.")
        else:
            # Generate logo from initials if blank
            if not logo_url.strip() and shop_name.strip():
                initials = "".join(word[0].upper() for word in shop_name.strip().split())
                logo_url = f"https://ui-avatars.com/api/?name={initials}&background=random"

            # Push to Firebase
            barber_ref.set({
                "config": {
                    "admin_pin": admin_pin or "0000"
                },
                "settings": {
                    "avg_cut_duration": avg_duration,
                    "open_hour": open_hour,
                    "close_hour": close_hour,
                    "shop_name": shop_name or "New Barber",
                    "logo_url": logo_url
                },
                "walkins": {},
                "bookings": {},
                "logs": {}
            })

            st.success(f"✅ Barber '{barber_id}' created successfully!")
            st.image(logo_url, caption="Logo preview", width=100)