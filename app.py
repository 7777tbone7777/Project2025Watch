# app.py

import streamlit as st
import pandas as pd
import datetime
import os
from utils import fetch_news_and_score_predictions, get_predictions_dataframe, trigger_emergency_alert, fetch_geopolitical_updates, generate_pdf_report, analyze_progress # Ensure analyze_progress is imported

# ... (rest of imports and initial config) ...

# --- Emergency Alerts and Progress Data ---
# ... (st.session_state.predictions_df and button logic) ...

# Ensure analyze_progress is called to get the progress data for alerts and bars
progress_data_for_alerts = analyze_progress() # Call analyze_progress here

alert = trigger_emergency_alert(progress_data_for_alerts) # Use the fetched progress data for alerts
if alert['triggered']:
    st.error(f"🚨 EMERGENCY ALERT: {alert['reason']}")
    st.markdown("### 🔐 Escape Readiness Guide (coming soon...)")

# --- Progress Bars (FIXED SECTION) ---
st.markdown("## 📊 Progress Toward Authoritarian Goals")

# Iterate through the progress_data to display each progress bar
for item in progress_data_for_alerts:
    st.subheader(item['title'])
    st.progress(item['progress'] / 100) # This line renders the progress bar
    st.caption(f"Progress: {item['progress']}% - Last Updated: {item['last_updated']}")

# --- Display Data (UPDATED to use the scored DataFrame) ---
st.title("📊 Project 2025 Prediction Tracker")
# ... (rest of your app.py, starting from the df display loop) ...
