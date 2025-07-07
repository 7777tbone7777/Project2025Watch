import pandas as pd
import datetime
import streamlit as st
from openai import OpenAI
import requests
import feedparser

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY"))

# Placeholder for News API
NEWS_API_BASE_URL = "https://newsapi.org/v2/everything"
NEWS_API_KEY = st.secrets.get("NEWS_API_KEY") # Access NEWS_API_KEY from st.secrets

AGENDA_CATEGORIES = [
    "Federal Agency Capture",
    "Judicial Defiance",
    "Suppression of Dissent",
    "NATO Disengagement",
    "Media Subversion"
]

# --- Prediction Loading ---
@st.cache_data
def get_predictions_dataframe():
    """
    Loads the Project 2025 predictions into a DataFrame.
    """
    predictions_data = [
        {"Timeframe": "Jan-Mar 2025", "Prediction": "Executive Order 1: Streamline Federal Bureaucracy", "Result": "Not Started", "News Match": ""},
        {"Timeframe": "Jan-Mar 2025", "Prediction": "Policy Change 1: Energy Deregulation", "Result": "Not Started", "News Match": ""},
        {"Timeframe": "Apr-Jun 2025", "Prediction": "Judicial Appointment 1: Conservative Judge", "Result": "Not Started", "News Match": ""},
        {"Timeframe": "Apr-Jun 2025", "Prediction": "Agency Restructuring 1: Department of Education changes", "Result": "Not Started", "News Match": ""},
        {"Timeframe": "Jul-Sep 2025", "Prediction": "Legislative Push 1: Immigration Reform", "Result": "Not Started", "News Match": ""},
        {"Timeframe": "Jul-Sep 2025", "Prediction": "Withdrawal from International Treaty", "Result": "Not Started", "News Match": ""},
        {"Timeframe": "Oct-Dec 2025", "Prediction": "Executive Order 2: Re-evaluating Environmental Regulations", "Result": "Not Started", "News Match": ""},
    ]
    df = pd.DataFrame(predictions_data)
    df['PredictionID'] = df.index
    return df

# --- News API Queries ---
def search_news(query, api_key):
    """
    Searches news articles using a generic News API.
    Returns a list of article summaries.
    """
    if not api_key:
        st.warning("NEWS_API_KEY not found in Streamlit Secrets. News fetching will not work.")
        return []

    params = {
        "q": query,
        "language": "en",
        "sortBy": "relevancy",
        "apiKey": api_key,
        "pageSize": 5 # Limit articles to process for performance
    }
    try:
        response = requests.get(NEWS_API_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        articles = []
        if data and data.get("articles"):
            for article in data["articles"]:
                if article.get("description"):
                    articles.append(article["title"] + ". " + article["description"])
        return articles
    except requests.exceptions.Timeout:
        st.error(f"News API request timed out for query: '{query}'")
        return []
    except requests.exceptions.HTTPError as e:
        st.error(f"News API HTTP error for query '{query}': {e}. Status code: {e.response.status_code}. Response: {e.response.text}")
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred fetching news for query '{query}': {e}")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred in news search for query '{query}': {e}")
        return []


# --- AI-based Status Scoring ---
@st.cache_data(ttl=600)
def score_prediction_status(prediction_text, news_summary):
    """
    Uses OpenAI to score the status of a prediction based on news summaries.
    """
    if not client.api_key:
        st.error("OpenAI API key not configured. Cannot score predictions.")
        return "Not Started"

    if not news_summary:
        return "Not Started"

    prompt = f"""
    You are an expert political analyst. Your task is to evaluate the status of a specific prediction based on recent news.
    The status can be one of the following: "Achieved", "InProgress", "Obstructed", "Not Started".

    Prediction: "{prediction_text}"

    Recent News Summary: "{news_summary}"

    Based on the news, what is the most appropriate status for the prediction?
    Return only one of the following words: Achieved, InProgress, Obstructed, Not Started.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a political analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=10
        )
        result = response.choices[0].message.content.strip()
        valid_results = ["Achieved", "InProgress", "Obstructed", "Not Started"]
        if result in valid_results:
            return result
        else:
            print(f"AI returned invalid result: '{result}'. Defaulting to 'Not Started'.")
            return "Not Started"

    except Exception as e:
        st.error(f"Error scoring with AI for prediction '{prediction_text}': {e}")
        st.exception(e) # RE-ENABLED for debugging
        return "Not Started"

# --- Main News Fetching and Scoring for DataFrame ---
@st.cache_data(show_spinner=False, ttl=600) # Cache the entire df update process
def fetch_news_and_score_predictions(df_predictions):
    """
    Fetches news for each prediction in the DataFrame and updates its status using AI.
    This replaces the previous fetch_geopolitical_updates function for the main scoring loop.
    """
    st.info("Starting news fetch and prediction scoring...")
    updated_predictions_list = []
    news_api_key = st.secrets.get("NEWS_API_KEY")

    for index, row in df_predictions.iterrows():
        prediction_text = row["Prediction"]
        st.info(f"Processing prediction: {prediction_text}") # Debug print
        
        # Formulate a search query based on the prediction
        # You might need to refine this for better news results relevant to Project 2025
        search_query = f"Project 2025 {prediction_text}"
        
        # Fetch news (using the generic search_news function)
        # Limiting to very few articles per query for initial testing performance
        news_summaries = search_news(search_query, news_api_key)
        
        combined_news_summary = "\n".join(news_summaries) if news_summaries else ""
        if not combined_news_summary:
            st.warning(f"No news found for '{prediction_text}'. Status will remain 'Not Started'.") # Debug print

        # Score the prediction status using AI
        new_status = score_prediction_status(prediction_text, combined_news_summary)

        # Update the DataFrame row
        updated_row = row.copy()
        updated_row["Result"] = new_status
        updated_row["News Match"] = combined_news_summary # Store the combined news for display if desired

        updated_predictions_list.append(updated_row)
    
    st.success("Finished processing all predictions.")
    return pd.DataFrame(updated_predictions_list)


# --- Functions below are separate from the main scoring loop, for displaying geopolitical updates ---
# These would be used if you wanted to display general geopolitical news separately from Project 2025 predictions.
# Based on your app.py, it seems you want to tie articles to specific predictions.

# The original fetch_geopolitical_updates is removed as its logic is merged into fetch_news_and_score_predictions
# However, if you want to explicitly keep fetching and tagging general geopolitical news for the "categorized" display,
# you would need to re-introduce and call a separate function for that in app.py.

# For now, let's assume the "events" that app.py iterates over come *from* the 'News Match' column of the df
# or need to be fetched separately. The app.py currently calls fetch_geopolitical_updates() for `events`.
# Let's keep a placeholder for `fetch_geopolitical_updates` if you still intend to use the RSS feeds.
# If these functions are NOT needed, you can remove them and update app.py accordingly.

# If you want to use RSS feeds for general geopolitical updates, then include this:
@st.cache_data(ttl=300)
def fetch_geopolitical_updates():
    """
    Fetches geopolitical news from RSS feeds and assigns tags using AI.
    This is separate from the Project 2025 prediction scoring.
    """
    rss_urls = [
        "http://feeds.reuters.com/Reuters/worldNews",
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://apnews.com/rss/apf-topnews"
    ]

    articles = []

    for url in rss_urls:
        feed = feedparser.parse(url)
        # TEMPORARY: Processing only 1 entry per feed for faster testing/debugging
        for entry in feed.entries[:1]: # Changed from :3 to :1 for testing
            title = entry.title
            summary = entry.summary if hasattr(entry, 'summary') else ""
            full_text = f"Title: {title}\nSummary: {summary}"
            
            try:
                # Use a different prompt for general tagging vs. prediction scoring
                tag = assign_tag_with_ai_general(full_text) # New tagging function for general news
            except Exception as e:
                st.error(f"Error during AI tagging for article '{title}': {e}")
                st.exception(e)
                tag = "Untagged (AI Error)"

            articles.append({
                "title": title,
                "date": datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d') if hasattr(entry, 'published_parsed') else "N/A",
                "summary": summary,
                "link": entry.link,
                "tags": [tag] if tag and tag != "None" else []
            })
    return articles

def assign_tag_with_ai_general(article_text):
    """
    Assigns a general category tag to an article using AI.
    (This function could be used by fetch_geopolitical_updates).
    """
    if not client.api_key:
        return "None" # No AI tagging if key missing

    system_prompt = (
        "You're a political analyst classifying news. "
        "Choose the ONE most relevant category from this list: "
        "Federal Agency Capture, Judicial Defiance, Suppression of Dissent, "
        "NATO Disengagement, Media Subversion. "
        "If none apply, return 'None'. Only return the category name."
    )
    user_prompt = f"Classify this article:\n{article_text}"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2, # A bit higher temperature might give more diverse tags
            max_tokens=20
        )
        tag = response.choices[0].message.content.strip()
        valid_tags = AGENDA_CATEGORIES # Use the defined categories
        return tag if tag in valid_tags else "None"
    except Exception as e:
        print(f"AI general tag error: {e}")
        st.exception(e)
        return "None"


# NOTE: `analyze_progress` and `trigger_emergency_alert` were in `utils.py` previously.
# Ensure they are correctly used by app.py based on your application design.
# If these functions are used by app.py, keep them here.
def analyze_progress():
    # This data is currently hardcoded and defines the progress bars.
    # In a real app, this would be updated by the news analysis.
    return [
        {"title": "Federal Agency Capture", "progress": 82, "last_updated": "2025-04-17"},
        {"title": "Judicial Defiance", "progress": 73, "last_updated": "2025-04-17"},
        {"title": "Suppression of Dissent", "progress": 78, "last_updated": "2025-04-17"},
        {"title": "NATO Disengagement", "progress": 43, "last_updated": "2025-04-17"},
        {"title": "Media Subversion", "progress": 54, "last_updated": "2025-04-17"},
    ]

def trigger_emergency_alert(progress_data):
    triggered = False
    reasons = []

    for item in progress_data:
        if item['title'] == "Federal Agency Capture" and item['progress'] >= 80:
            reasons.append("Federal agency capture exceeds safe threshold.")
        if item['title'] == "Judicial Defiance" and item['progress'] >= 70:
            reasons.append("Unconstitutional judicial defiance observed.")
        if item['title'] == "Suppression of Dissent" and item['progress'] >= 75:
            reasons.append("Active suppression of dissent detected.")

    if reasons:
        return {"triggered": True, "reason": " | ".join(reasons)}
    return {"triggered": False, "reason": ""}

# PDF generation function (if still needed here)
def generate_pdf_report(progress_data, events):
    from fpdf import FPDF
    import tempfile

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Dugin-Trump Weekly Intelligence Report", ln=True, align="C")

    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="Progress Overview", ln=True)
    pdf.set_font("Arial", size=11)
    for item in progress_data:
        pdf.cell(200, 8, txt=f"{item['title']}: {item['progress']}% (Last Updated: {item['last_updated']})", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="Recent Events", ln=True)
    pdf.set_font("Arial", size=11)
    for event in events:
        pdf.cell(200, 8, txt=f"{event['title']} ({event['date']})", ln=True)
        summary_text = str(event['summary']).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 8, txt=summary_text)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    return temp.name
