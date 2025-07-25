import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import pandas as pd
import plotly.express as px

# --- Firebase init ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {'databaseURL': st.secrets["firebase_db_url"]})

walkin_ref = db.reference("walkins")
booking_ref = db.reference("bookings")

st.set_page_config(page_title="Barber Dashboard", layout="wide")
st.title("📊 Barber Dashboard")

walkins = walkin_ref.get() or {}
bookings = booking_ref.get() or {}

if not walkins and not bookings:
    st.info("No walk-ins or bookings yet.")
    st.stop()

# --- Combine data ---
combined = []
for _, w in walkins.items():
    combined.append({"name": w["name"], "joined_at": w["joined_at"], "source": "walkin"})
for _, b in bookings.items():
    combined.append({"name": b["name"], "joined_at": b["slot"], "source": "booking"})

df = pd.DataFrame(combined)
df = df[df['joined_at'].notnull()]
df['joined_at'] = pd.to_datetime(df['joined_at'], errors='coerce')
df = df.dropna(subset=['joined_at'])
df['date'] = df['joined_at'].dt.date
df['hour'] = df['joined_at'].dt.floor('H')
df = df.sort_values('joined_at')

# --- Stats ---
st.subheader("📈 Key Stats")

st.metric("👥 Total People", len(df))
st.metric("🧑‍🦱 Walk-ins", (df['source'] == 'walkin').sum())
st.metric("📅 Bookings", (df['source'] == 'booking').sum())

first = df.iloc[0]['joined_at']
now = datetime.now()
wait_time = (now - first).seconds // 60
st.metric("⏳ Longest Wait Time", f"{wait_time} mins")

# --- Daily Chart (Interactive) ---
st.divider()
st.subheader("📅 Weekly Engagement – Walk-ins vs Bookings")

daily_counts = df.groupby(['date', 'source']).size().unstack(fill_value=0).reset_index()

fig = px.bar(
    daily_counts,
    x='date',
    y=['walkin', 'booking'],
    title="Bookings vs Walk-ins per Day",
    labels={'value': 'Number of People', 'date': 'Date'},
    barmode='stack'
)
fig.update_layout(xaxis_title="Date", yaxis_title="People", legend_title="Type")

st.plotly_chart(fig, use_container_width=True)

import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import pandas as pd
import plotly.express as px

# --- Firebase init ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase_creds"]))
    firebase_admin.initialize_app(cred, {'databaseURL': st.secrets["firebase_db_url"]})

walkin_ref = db.reference("walkins")
booking_ref = db.reference("bookings")

st.set_page_config(page_title="Barber Dashboard", layout="wide")
st.title("📊 Barber Dashboard")

walkins = walkin_ref.get() or {}
bookings = booking_ref.get() or {}

if not walkins and not bookings:
    st.info("No walk-ins or bookings yet.")
    st.stop()

# --- Combine data ---
combined = []
for _, w in walkins.items():
    combined.append({"name": w["name"], "joined_at": w["joined_at"], "source": "walkin"})
for _, b in bookings.items():
    combined.append({"name": b["name"], "joined_at": b["slot"], "source": "booking"})

df = pd.DataFrame(combined)
df = df[df['joined_at'].notnull()]
df['joined_at'] = pd.to_datetime(df['joined_at'], errors='coerce')
df = df.dropna(subset=['joined_at'])
df['date'] = df['joined_at'].dt.date
df['hour'] = df['joined_at'].dt.floor('H')
df = df.sort_values('joined_at')

# --- Stats ---
st.subheader("📈 Key Stats")

st.metric("👥 Total People", len(df))
st.metric("🧑‍🦱 Walk-ins", (df['source'] == 'walkin').sum())
st.metric("📅 Bookings", (df['source'] == 'booking').sum())

first = df.iloc[0]['joined_at']
now = datetime.now()
wait_time = (now - first).seconds // 60
st.metric("⏳ Longest Wait Time", f"{wait_time} mins")

# --- Daily Chart (Interactive) ---
st.divider()
st.subheader("📅 Weekly Engagement – Walk-ins vs Bookings")

daily_counts = df.groupby(['date', 'source']).size().unstack(fill_value=0).reset_index()

# Ensure both columns exist to prevent Plotly error
for col in ['walkin', 'booking']:
    if col not in daily_counts.columns:
        daily_counts[col] = 0

fig = px.bar(
    daily_counts,
    x='date',
    y=['walkin', 'booking'],
    title="Bookings vs Walk-ins per Day",
    labels={'value': 'Number of People', 'date': 'Date'},
    barmode='stack'
)
fig.update_layout(xaxis_title="Date", yaxis_title="People", legend_title="Type")

st.plotly_chart(fig, use_container_width=True)