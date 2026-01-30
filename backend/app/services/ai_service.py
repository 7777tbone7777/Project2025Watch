from typing import Optional
from openai import OpenAI
from app.config import settings

AGENDA_CATEGORIES = [
    "Federal Agency Capture",
    "Judicial Defiance",
    "Suppression of Dissent",
    "NATO Disengagement",
    "Media Subversion",
]


def get_openai_client() -> Optional[OpenAI]:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def score_prediction_status(prediction_text: str, news_summary: str) -> str:
    """Score a prediction based on news summary using OpenAI."""
    client = get_openai_client()
    if not client:
        print("ERROR: OpenAI API key not configured")
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
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=10,
        )
        result = response.choices[0].message.content.strip()
        valid_results = ["Achieved", "InProgress", "Obstructed", "Not Started"]
        if result in valid_results:
            return result
        print(f"AI returned invalid result: '{result}'. Defaulting to 'Not Started'.")
        return "Not Started"

    except Exception as e:
        print(f"ERROR: Exception during OpenAI scoring: {e}")
        return "Not Started"


def assign_tag_with_ai(article_text: str) -> str:
    """Classify an article into one of the agenda categories."""
    client = get_openai_client()
    if not client:
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
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=20,
        )
        tag = response.choices[0].message.content.strip()
        return tag if tag in AGENDA_CATEGORIES else "None"
    except Exception as e:
        print(f"ERROR: Exception during AI tagging: {e}")
        return "None"


def analyze_category_progress(category: str, news_summary: str) -> int:
    """Analyze progress percentage for a category based on recent news."""
    client = get_openai_client()
    if not client:
        print("ERROR: OpenAI API key not configured")
        return 0

    if not news_summary:
        return 0

    category_descriptions = {
        "Federal Agency Capture": "the extent to which federal agencies have been taken over by political loyalists, career staff replaced, and agency independence compromised",
        "Judicial Defiance": "instances where the executive branch has ignored, defied, or undermined court rulings and judicial independence",
        "Suppression of Dissent": "actions to silence critics, restrict protests, target journalists, or intimidate opposition voices",
        "NATO Disengagement": "steps to weaken NATO alliances, reduce commitments to allies, or align with adversarial nations",
        "Media Subversion": "efforts to discredit mainstream media, promote state-aligned narratives, or control information flow",
    }

    description = category_descriptions.get(category, category)

    prompt = f"""You are an expert political analyst tracking authoritarian indicators in the United States.

Category: {category}
Definition: {description}

Recent News Summary:
{news_summary}

Based on the news above, estimate the progress toward this authoritarian goal as a percentage from 0 to 100.
- 0% means no progress, situation is normal/healthy
- 25% means early warning signs
- 50% means significant concerning developments
- 75% means serious erosion of democratic norms
- 100% means complete authoritarian capture in this area

Return ONLY a number between 0 and 100, nothing else."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a political analyst. Return only a number."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=10,
        )
        result = response.choices[0].message.content.strip()
        # Extract number from response
        import re
        match = re.search(r'\d+', result)
        if match:
            progress = int(match.group())
            return min(100, max(0, progress))  # Clamp between 0-100
        return 0
    except Exception as e:
        print(f"ERROR: Exception during progress analysis: {e}")
        return 0
