import pandas as pd
import datetime
import streamlit as st
from openai import OpenAI
import requests
import feedparser # Added feedparser import

# Initialize OpenAI client
# When deploying on Streamlit, st.secrets is automatically loaded.
# Ensure OPENAI_API_KEY is configured in Streamlit Cloud Secrets.
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY"))

# Placeholder for News API (replace with your actual News API client/logic)
# Ensure NEWS_API_KEY is configured in Streamlit Cloud Secrets.
NEWS_API_BASE_URL = "https://newsapi.org/v2/everything" # Example News API base URL
# Access NEWS_API_KEY using st.secrets
NEWS_API_KEY = st.secrets.get("NEWS_API_KEY") 

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
    In a real application, this would load from a persistent source (DB, CSV, Google Sheet).
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
    # Add a unique ID for each prediction for easier tracking if needed
    df['PredictionID'] = df.index
    return df

# --- News API Queries ---
def search_news(query, api_key):
    """
    Searches news articles using a generic News API.
    Replace with specific client/methods for your chosen News API.
    Returns a list of article summaries.
    """
    if not api_key:
        st.warning("NEWS_API_KEY not found in Streamlit Secrets. News fetching will not work.")
        return []

    # Example for NewsAPI.org - adjust if using a different API
    params = {
        "q": query,
        "language": "en",
        "sortBy": "relevancy",
        "apiKey": api_key,
        "pageSize": 5 # Limit articles to process for performance
    }
    try:
        response = requests.get(NEWS_API_BASE_URL, params=params, timeout=10)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        articles = []
        if data and data.get("articles"):
            for article in data["articles"]:
                # Ensure 'description' key exists and is not None
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
@st.cache_data(ttl=600) # Cache scores for 10 minutes
def score_prediction_status(prediction_text, news_summary):
    """
    Uses OpenAI to score the status of a prediction based on news summaries.
    Possible results: Achieved, InProgress, Obstructed, Not Started.
    """
    if not client.api_key:
        st.error("OpenAI API key not configured. Cannot score predictions.")
        return "Not Started" # Default if API key is missing

    if not news_summary:
        return "Not Started" # If no relevant news, assume not started or progress can't be determined

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
            model="gpt-3.5-turbo", # Using gpt-3.5-turbo for cost-effectiveness and speed, can change to gpt-4
            messages=[
                {"role": "system", "content": "You are a political analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0, # Keep low for deterministic results
            max_tokens=10
        )
        result = response.choices[0].message.content.strip()
        # Validate result against expected categories
        valid_results = ["Achieved", "InProgress", "Obstructed", "Not Started"]
        if result in valid_results:
            return result
        else:
            print(f"AI returned invalid result: '{result}'. Defaulting to 'Not Started'.")
            return "Not Started"

    except Exception as e:
        st.error(f"Error scoring with AI for prediction '{prediction_text}': {e}")
        st.exception(e) # RE-ENABLED for debugging
        return "Not Started" # Default in case of AI error


@st.cache_data(show_spinner=False)
def fetch_geopolitical_updates():
    """
    Fetches geopolitical news from RSS feeds and assigns tags.
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
        # REMEMBER TO CHANGE THIS BACK TO :3 or more for full functionality.
        for entry in feed.entries[:1]: # Changed from :3 to :1 for testing
            title = entry.title
            summary = entry.summary if hasattr(entry, 'summary') else ""
            full_text = f"Title: {title}\nSummary: {summary}"
            
            # Catch potential errors from AI tagging and make them visible
            try:
                tag = assign_tag_with_ai(full_text)
            except Exception as e:
                st.error(f"Error during AI tagging for article '{title}': {e}")
                st.exception(e) # RE-ENABLED for debugging
                tag = "Untagged (AI Error)" # Assign a tag to indicate error

            articles.append({
                "title": title,
                "date": datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d') if hasattr(entry, 'published_parsed') else "N/A",
                "summary": summary,
                "link": entry.link,
                "tags": [tag] if tag and tag != "None" else [] # Ensure "None" string isn't added as a tag
            })

    return articles

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
        # Ensure summary is a string, then encode for fpdf compatibility
        summary_text = str(event['summary']).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 8, txt=summary_text)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    return temp.name
