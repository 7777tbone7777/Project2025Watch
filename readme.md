# Project 2025 Tracker

This Streamlit application monitors the implementation of "Project 2025" predictions by cross-referencing them with recent news, leveraging AI for status scoring.

## Features

- **Dynamic Prediction Tracking:** Displays key predictions for Project 2025 across different timeframes.
- **News Integration:** Fetches relevant news articles based on prediction keywords.
- **AI-Powered Scoring:** Uses OpenAI's GPT models to determine the status of each prediction (Achieved, InProgress, Obstructed, Not Started) based on the fetched news.
- **Interactive UI:** A Streamlit interface to view predictions, trigger news checks, and see score summaries.

## How to Run Locally

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/7777tbone7777/your-repo-name.git](https://github.com/7777tbone7777/your-repo-name.git)
    cd your-repo-name # Replace with your actual repository name
    ```
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up environment variables:**
    Create a file named `.env` in the root of your project directory (the same folder as `app.py`). Add your API keys to this file:
    ```
    OPENAI_API_KEY="your_openai_api_key_here"
    NEWS_API_KEY="your_news_api_key_here" # Only if you are using a News API that requires a key
    ```
    Replace `"your_openai_api_key_here"` and `"your_news_api_key_here"` with your actual API keys. **Do not commit this `.env` file to Git!** Add `.env` to your `.gitignore` file.
5.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```
    This will open the application in your web browser.

## Deployment on Streamlit Community Cloud (streamlit.io)

For secure deployment on Streamlit Community Cloud, you must configure your API keys as "Secrets" directly in the Streamlit Cloud dashboard, rather than using a `.env` file.

1.  **Prepare your `app.py` and `utils.py`:** Ensure they access API keys using `st.secrets["YOUR_KEY_NAME"]`. (The provided `app.py` and `utils.py` already do this).
2.  **Commit your code to GitHub:** Make sure `app.py`, `utils.py`, and `requirements.txt` are pushed to your GitHub repository. **Ensure your `.env` file is NOT committed.**
3.  **Go to Streamlit Community Cloud:** Log in at [https://share.streamlit.io/](https://share.streamlit.io/).
4.  **Create a new app** (or select your existing one).
5.  **Connect to your GitHub repository.**
6.  **Configure Secrets:**
    * In the app's settings (usually a gear icon or "Settings" button), navigate to the **"Secrets"** section.
    * Add your API keys in the TOML format. **Crucially, if your keys contain underscores, you must quote them:**
        ```toml
        "OPENAI_API_KEY"="your_openai_api_key_here"
        "NEWS_API_KEY"="your_news_api_key_here" # Only if you are using a News API that requires a key
        ```
    * Click "Save secrets".
7.  **Deploy your app.** Streamlit will build and run your app, automatically injecting the secrets.

## Important Considerations

* **API Rate Limits:** Be mindful of API rate limits for both OpenAI and your chosen News API. Adjust `pageSize` in `utils.py` and caching `ttl` values if you encounter rate limiting.
* **Cost:** OpenAI API calls incur costs. Monitor your OpenAI usage.
* **News API Choice:** The `search_news` function is currently a generic placeholder. You might need to adjust it significantly based on the specific News API service you choose to use (e.g., NewsAPI.org, New York Times API, etc.). Ensure you sign up for an API key with your chosen service.
