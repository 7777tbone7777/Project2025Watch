import pandas as pd
import datetime
import os
import streamlit as st # Used for st.secrets and st.cache_data
from openai import OpenAI # Newer OpenAI client library syntax
import requests # For News API queries (generic placeholder)

# Initialize OpenAI client
# When deploying on Streamlit, st.secrets is automatically loaded.
# Ensure OPENAI_API_KEY is configured in Streamlit Cloud Secrets.
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY"))

# Placeholder for News API (replace with your actual News API client/logic)
# Ensure NEWS_API_KEY is configured in Streamlit Cloud Secrets.
NEWS_API_BASE_URL = "https://newsapi.org/v2/everything" # Example News API base URL
# NEWS_API_KEY = st.secrets.get("NEWS_API_KEY") # Uncomment and use if you have a News API Key

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
        return "Not Started" # Default in case of AI error


@st.cache_data(show_spinner=False)
def fetch_news_and_score_predictions(df_predictions):
    """
    Fetches news for each prediction and updates its status using AI.
    """
    updated_predictions = []
    news_api_key = st.secrets.get("NEWS_API_KEY") # Access NEWS_API_KEY here

    for index, row in df_predictions.iterrows():
        prediction_text = row["Prediction"]
        timeframe = row["Timeframe"]

        # Formulate a search query based on the prediction
        # You might need to refine this for better news results
        search_query = f"Project 2025 {prediction_text}"
        
        # Fetch news (using the generic search_news function)
        news_summaries = search_news(search_query, news_api_key)
        
        combined_news_summary = "\n".join(news_summaries) if news_summaries else ""

        # Score the prediction status using AI
        new_status = score_prediction_status(prediction_text, combined_news_summary)

        # Update the DataFrame row
        updated_row = row.copy()
        updated_row["Result"] = new_status
        updated_row["News Match"] = combined_news_summary # Store the combined news for display if desired

        updated_predictions.append(updated_row)

    return pd.DataFrame(updated_predictions)
