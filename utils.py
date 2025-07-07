import pandas as pd
import datetime
import streamlit as st
from openai import OpenAI
import requests
import feedparser

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY"))
print(f"DEBUG: OpenAI API Key loaded: {'Yes' if client.api_key else 'No'}") # Debug print

# Placeholder for News API (replace with your actual News API client/logic)
NEWS_API_BASE_URL = "https://newsapi.org/v2/everything" # Example News API base URL
NEWS_API_KEY = st.secrets.get("NEWS_API_KEY") # Access NEWS_API_KEY from st.secrets
print(f"DEBUG: News API Key loaded: {'Yes' if NEWS_API_KEY else 'No'}") # Debug print

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
    # ... (function body remains the same) ...
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
    print("DEBUG: Predictions DataFrame loaded.") # Debug print
    return df

# --- News API Queries ---
def search_news(query, api_key):
    print(f"DEBUG: Calling search_news for query: '{query}'") # Debug print
    if not api_key:
        st.warning("NEWS_API_KEY not found in Streamlit Secrets. News fetching will not work.")
        print("ERROR: NEWS_API_KEY is None in search_news.") # Debug print
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
        print(f"DEBUG: News API response status: {response.status_code}, articles found: {len(data.get('articles', []))}") # Debug print
        articles = []
        if data and data.get("articles"):
            for article in data["articles"]:
                if article.get("description"):
                    articles.append(article["title"] + ". " + article["description"])
        return articles
    except requests.exceptions.Timeout:
        st.error(f"News API request timed out for query: '{query}'")
        print(f"ERROR: News API Timeout for '{query}'.") # Debug print
        return []
    except requests.exceptions.HTTPError as e:
        st.error(f"News API HTTP error for query '{query}': {e}. Status code: {e.response.status_code}. Response: {e.response.text}")
        print(f"ERROR: News API HTTP Error for '{query}': {e.response.status_code}") # Debug print
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred fetching news for query '{query}': {e}")
        print(f"ERROR: News API Request Exception for '{query}': {e}.") # Debug print
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred in news search for query '{query}': {e}")
        print(f"ERROR: Unexpected error in news search for '{query}': {e}.") # Debug print
        return []


# --- AI-based Status Scoring ---
@st.cache_data(ttl=600)
def score_prediction_status(prediction_text, news_summary):
    print(f"DEBUG: Calling score_prediction_status for: '{prediction_text}' (News summary length: {len(news_summary)})") # Debug print
    if not client.api_key:
        st.error("OpenAI API key not configured. Cannot score predictions.")
        print("ERROR: OpenAI API key is None in score_prediction_status.") # Debug print
        return "Not Started"

    if not news_summary:
        print(f"DEBUG: No news summary for '{prediction_text}', returning 'Not Started'.") # Debug print
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
        print(f"DEBUG: OpenAI returned result: '{result}' for '{prediction_text}'.") # Debug print
        valid_results = ["Achieved", "InProgress", "Obstructed", "Not Started"]
        if result in valid_results:
            return result
        else:
            print(f"AI returned invalid result: '{result}'. Defaulting to 'Not Started'.")
            return "Not Started"

    except Exception as e:
        st.error(f"Error scoring with AI for prediction '{prediction_text}': {e}")
        st.exception(e) # RE-ENABLED for debugging
        print(f"ERROR: Exception during OpenAI scoring for '{prediction_text}': {e}.") # Debug print
        return "Not Started"


# --- Main News Fetching and Scoring for DataFrame ---
@st.cache_data(show_spinner=False, ttl=600)
def fetch_news_and_score_predictions(df_predictions):
    st.info("Starting news fetch and prediction scoring...")
    print("DEBUG: fetch_news_and_score_predictions started.") # Debug print
    updated_predictions_list = []
    news_api_key = st.secrets.get("NEWS_API_KEY")

    for index, row in df_predictions.iterrows():
        prediction_text = row["Prediction"]
        st.info(f"Processing prediction: {prediction_text}")
        print(f"DEBUG: Processing prediction loop: '{prediction_text}'") # Debug print
        
        search_query = f"Project 2025 {prediction_text}"
        
        news_summaries = search_news(search_query, news_api_key)
        
        combined_news_summary = "\n".join(news_summaries) if news_summaries else ""
        if not combined_news_summary:
            st.warning(f"No news found for '{prediction_text}'. Status will remain 'Not Started'.")
            print(f"DEBUG: No combined news summary for '{prediction_text}'.") # Debug print

        new_status = score_prediction_status(prediction_text, combined_news_summary)

        updated_row = row.copy()
        updated_row["Result"] = new_status
        updated_row["News Match"] = combined_news_summary

        updated_predictions_list.append(updated_row)
    
    st.success("Finished processing all predictions.")
    print("DEBUG: fetch_news_and_score_predictions finished.") # Debug print
    return pd.DataFrame(updated_predictions_list)


@st.cache_data(ttl=300)
def fetch_geopolitical_updates():
    print("DEBUG: fetch_geopolitical_updates (RSS) started.") # Debug print
    rss_urls = [
        "http://feeds.reuters.com/Reuters/worldNews",
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://apnews.com/rss/apf-topnews"
    ]

    articles = []

    for url in rss_urls:
        print(f"DEBUG: Fetching RSS feed from: {url}") # Debug print
        feed = feedparser.parse(url)
        print(f"DEBUG: RSS feed '{url}' has {len(feed.entries)} entries. Processing up to 1.") # Debug print
        for entry in feed.entries[:1]:
            title = entry.title
            summary = entry.summary if hasattr(entry, 'summary') else ""
            full_text = f"Title: {title}\nSummary: {summary}"
            
            try:
                tag = assign_tag_with_ai_general(full_text)
            except Exception as e:
                st.error(f"Error during AI tagging for article '{title}': {e}")
                st.exception(e)
                print(f"ERROR: Exception during general AI tagging for '{title}': {e}.") # Debug print
                tag = "Untagged (AI Error)"

            articles.append({
                "title": title,
                "date": datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d') if hasattr(entry, 'published_parsed') else "N/A",
                "summary": summary,
                "link": entry.link,
                "tags": [tag] if tag and tag != "None" else []
            })
    print("DEBUG: fetch_geopolitical_updates (RSS) finished.") # Debug print
    return articles

def assign_tag_with_ai_general(article_text):
    print(f"DEBUG: Calling assign_tag_with_ai_general (Article text length: {len(article_text)})") # Debug print
    if not client.api_key:
        print("ERROR: OpenAI API key is None in assign_tag_with_ai_general.") # Debug print
        return "None"

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
            temperature=0.2,
            max_tokens=20
        )
        tag = response.choices[0].message.content.strip()
        print(f"DEBUG: General AI tag returned: '{tag}'.") # Debug print
        valid_tags = AGENDA_CATEGORIES
        return tag if tag in valid_tags else "None"
    except Exception as e:
        print(f"ERROR: Exception during general AI tagging: {e}.") # Debug print
        st.exception(e)
        return "None"


def analyze_progress():
    print("DEBUG: analyze_progress called.") # Debug print
    return [
        {"title": "Federal Agency Capture", "progress": 82, "last_updated": "2025-04-17"},
        {"title": "Judicial Defiance", "progress": 73, "last_updated": "2025-04-17"},
        {"title": "Suppression of Dissent", "progress": 78, "last_updated": "2025-04-17"},
        {"title": "NATO Disengagement", "progress": 43, "last_updated": "2025-04-17"},
        {"title": "Media Subversion", "progress": 54, "last_updated": "2025-04-17"},
    ]

def trigger_emergency_alert(progress_data):
    print("DEBUG: trigger_emergency_alert called.") # Debug print
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
    print("DEBUG: generate_pdf_report called.") # Debug print
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
    print(f"DEBUG: PDF report generated at {temp.name}.") # Debug print
    return temp.name
