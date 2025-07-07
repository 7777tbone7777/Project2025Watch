# app.py

import streamlit as st
import pandas as pd
import datetime
import os
from utils import fetch_news_and_score_predictions, get_predictions_dataframe, trigger_emergency_alert # No need for fetch_geopolitical_updates directly here for now

st.set_page_config(page_title="Project 2025 Tracker", layout="wide")
st.sidebar.title("🧭 Project 2025 Timeline")
st.sidebar.markdown("Monitoring the implementation of Project 2025, month by month.")

# --- Load Predictions (Initial State) ---
# Store the DataFrame in session state so it persists across reruns
if 'predictions_df' not in st.session_state:
    st.session_state.predictions_df = get_predictions_dataframe()

df = st.session_state.predictions_df

# --- News Matching & Auto-Scoring Button ---
st.sidebar.markdown("---")
if st.sidebar.button("🔍 Run Weekly News Check"):
    with st.spinner("Fetching news and scoring predictions..."):
        # This function updates the DataFrame based on news analysis
        st.session_state.predictions_df = fetch_news_and_score_predictions(df.copy()) # Pass a copy to avoid mutation issues with caching
    st.success("News sync complete. Predictions updated.")
    df = st.session_state.predictions_df # Update df to reflect changes

# --- Emergency Alerts (Based on *actual* progress, which we'll derive from df) ---
# For now, progress_data for alerts will still come from hardcoded analyze_progress
# As integrating AI-based progress into these alerts requires more complex scoring.
progress_data_for_alerts = [
    {"title": "Federal Agency Capture", "progress": (df[df['Prediction'].str.contains("Federal Agency", na=False)]['Result'] == 'Achieved').sum() * 100 / len(df[df['Prediction'].str.contains("Federal Agency", na=False)]), "last_updated": datetime.date.today().strftime('%Y-%m-%d')},
    # ... Add more sophisticated mapping from df['Result'] to overall progress here ...
    # For now, let's keep it simple or use the hardcoded analyze_progress temporarily
]
# Using the hardcoded analyze_progress for alerts for simplicity for now
progress_data_for_alerts = [
    {"title": "Federal Agency Capture", "progress": 82, "last_updated": "2025-04-17"},
    {"title": "Judicial Defiance", "progress": 73, "last_updated": "2025-04-17"},
    {"title": "Suppression of Dissent", "progress": 78, "last_updated": "2025-04-17"},
    {"title": "NATO Disengagement", "progress": 43, "last_updated": "2025-04-17"},
    {"title": "Media Subversion", "progress": 54, "last_updated": "2025-04-17"},
]
alert = trigger_emergency_alert(progress_data_for_alerts) # Using the hardcoded data for alerts
if alert['triggered']:
    st.error(f"🚨 EMERGENCY ALERT: {alert['reason']}")
    st.markdown("### 🔐 Escape Readiness Guide (coming soon...)")

# --- Display Data (UPDATED to use the scored DataFrame) ---
st.title("📊 Project 2025 Prediction Tracker")
for timeframe in df['Timeframe'].unique():
    st.subheader(f"Timeframe: {timeframe}")
    subset = df[df['Timeframe'] == timeframe].reset_index(drop=True)
    
    # Display the dataframe with updated results
    st.dataframe(subset, use_container_width=True)

    # Display associated news for each prediction within this timeframe
    for idx, row in subset.iterrows():
        if row['News Match']:
            with st.expander(f"News for: {row['Prediction']} (Status: {row['Result']})"):
                # The 'News Match' column in df currently stores a combined summary.
                # If you want original article titles/links, fetch_news_and_score_predictions
                # would need to return a more structured object including links.
                st.write(row['News Match'])
                # If you want original links to show here, you'd need to modify `fetch_news_and_score_predictions`
                # to return them, possibly as a list of dicts: `[{"title": "...", "link": "..."}]`
                # and then iterate and markdown those.
        else:
            st.caption(f"No relevant news found for '{row['Prediction']}' yet.")

# --- Score Summary ---
st.markdown("---")
st.header("📈 Tracker Scorecard")
score_counts = df['Result'].value_counts()
st.write(score_counts.to_frame(name="Count"))

# --- General Updates (Uncategorized) ---
# This part of app.py needs to decide where 'events' come from if not from fetch_geopolitical_updates.
# If you removed fetch_geopolitical_updates from utils.py, you need to remove this section or
# provide a new source for general news.
# For now, assuming you still want general news, and fetch_geopolitical_updates is in utils.py
from utils import fetch_geopolitical_updates # Re-import if it's separate from main scoring logic

# Fetch general geopolitical updates for the uncategorized section
general_events = fetch_geopolitical_updates() # This will run on every app load / reruns

ungrouped_articles = [e for e in general_events if not e.get('tags') or len(e.get('tags', [])) == 0]
if ungrouped_articles:
    st.markdown("## 🗃️ General Updates (Uncategorized)")
    for article in ungrouped_articles:
        st.markdown(f"**[{article['title']}]({article['link']})** ({article['date']})")
        st.write(article['summary'])
else:
    st.markdown("## 🗃️ General Updates (Uncategorized)")
    st.info("No uncategorized general news articles found, or all were tagged.")

# --- Export Report (Placeholder, ensure generate_pdf_report is imported) ---
from utils import generate_pdf_report # Ensure this is imported

st.markdown("## 📄 Generate Weekly Intelligence Report")
if st.button("Export PDF Report"):
    with st.spinner("Generating PDF report..."):
        # Pass the current state of the predictions DataFrame (df)
        report_path = generate_pdf_report(df.to_dict('records'), general_events) # Convert df to list of dicts
    with open(report_path, "rb") as file:
        st.download_button(
            label="Download Report",
            data=file,
            file_name="Project_2025_Weekly_Report.pdf",
            mime="application/pdf"
        )
    os.remove(report_path) # Clean up temporary PDF file


# Footer
st.caption(f"📅 Last App Rendered: {datetime.datetime.now().strftime('%B %d, %Y %H:%M:%S')}")
