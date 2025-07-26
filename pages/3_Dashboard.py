import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
from zoneinfo import ZoneInfo
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
df['joined_at'] = pd.to_datetime(df['joined_at'], errors='coerce').dt.tz_convert("Europe/London") if df['joined_at'].dt.tz else pd.to_datetime(df['joined_at'], utc=True).dt.tz_convert("Europe/London")
df = df.dropna(subset=['joined_at'])
df['date'] = df['joined_at'].dt.date
df['hour'] = df['joined_at'].dt.floor('h')  # changed from 'H' to 'h' to prevent future warning
df = df.sort_values('joined_at')

# --- Stats ---
st.subheader("📈 Key Stats")

st.metric("👥 Total People", len(df))
st.metric("🧑‍🦱 Walk-ins", (df['source'] == 'walkin').sum())
st.metric("📅 Bookings", (df['source'] == 'booking').sum())

first = df.iloc[0]['joined_at']
now = datetime.now(ZoneInfo("Europe/London"))
wait_time = (now - first).seconds // 60
st.metric("⏳ Longest Wait Time", f"{wait_time} mins")

# --- Daily Chart (Interactive) ---
st.divider()
st.subheader("📅 Weekly Engagement – Walk-ins vs Bookings")

daily_counts = df.groupby(['date', 'source']).size().unstack(fill_value=0).reset_index()
available_sources = [col for col in ['walkin', 'booking'] if col in daily_counts.columns]

fig = px.bar(
    daily_counts,
    x='date',
    y=available_sources,
    title="Bookings vs Walk-ins per Day",
    labels={'value': 'Number of People', 'date': 'Date'},
    barmode='stack'
)
fig.update_layout(xaxis_title="Date", yaxis_title="People", legend_title="Type")

st.plotly_chart(fig, use_container_width=True)

# --- Hourly Popularity Chart by Day of Week ---
st.divider()
st.subheader("📆 Popular Hours by Day (Walk-ins vs Bookings)")

df['day_of_week'] = df['joined_at'].dt.day_name()
df['hour_of_day'] = df['joined_at'].dt.hour

hourly_counts = df.groupby(['day_of_week', 'hour_of_day', 'source']).size().unstack(fill_value=0).reset_index()

# Keep only booking hours (10:00 to 21:00)
hourly_counts = hourly_counts[(hourly_counts['hour_of_day'] >= 10) & (hourly_counts['hour_of_day'] <= 21)]

# Ensure consistent weekday order
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
hourly_counts['day_of_week'] = pd.Categorical(hourly_counts['day_of_week'], categories=day_order, ordered=True)
hourly_counts = hourly_counts.sort_values(['day_of_week', 'hour_of_day'])

for day in day_order:
    day_df = hourly_counts[hourly_counts['day_of_week'] == day]
    if day_df.empty:
        continue

    available_sources = [col for col in ['walkin', 'booking'] if col in day_df.columns]

    fig = px.bar(
        day_df,
        x='hour_of_day',
        y=available_sources,
        title=f"{day}",
        labels={'hour_of_day': 'Hour', 'value': 'Number of People'},
        barmode='stack',
        height=300
    )
    fig.update_layout(
        xaxis=dict(dtick=1, tickmode='linear', range=[10, 21]),
        yaxis_title="People",
        legend_title="Type"
    )
    st.plotly_chart(fig, use_container_width=True)