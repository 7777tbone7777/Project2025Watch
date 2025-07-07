# app.py

import streamlit as st
import pandas as pd
import datetime
import os
from utils import fetch_news_and_score_predictions, get_predictions_dataframe

# --- App Config ---

st.set_page_config(page_title="Project 2025 Tracker", layout="wide")
st.sidebar.title("🧭 Project 2025 Timeline")
st.sidebar.markdown("Monitoring the implementation of Project 2025, month by month.")

# --- Load Predictions ---

df = get_predictions_dataframe()

# --- News Matching & Auto-Scoring ---

if st.sidebar.button("🔍 Run Weekly News Check"):
    with st.spinner("Fetching news and scoring predictions..."):
        df = fetch_news_and_score_predictions(df)
    st.success("News sync complete. Predictions updated.")

# --- Display Data ---

st.title("📊 Project 2025 Prediction Tracker")
for timeframe in df['Timeframe'].unique():
    st.subheader(timeframe)
    subset = df[df['Timeframe'] == timeframe].reset_index(drop=True)
    st.dataframe(subset, use_container_width=True)

# --- Score Summary ---

st.markdown("---")
st.header("📈 Tracker Scorecard")
score_counts = df['Result'].value_counts()
st.write(score_counts.to_frame(name="Count"))
