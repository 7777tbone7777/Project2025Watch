"""AI scoring for predictions and agenda categories.

Two changes that matter to whether the output can be trusted:

MODEL. Everything ran on gpt-3.5-turbo, which produced statuses that did not
survive a glance at the underlying articles — public broadcasting defunding came
back "Obstructed" when reporting said otherwise. gpt-4o-mini is far better at this
and still cheap.

REASONING. The old prompt returned a bare label with max_tokens=10, so there was
no way to tell a well-grounded call from a coin flip. Scores now come back with a
one-line justification citing what the model relied on. That makes a wrong call
visible instead of authoritative-looking, which matters for a tracker whose entire
value is that a sceptic can check it.
"""
import json
import logging
import re
from typing import Optional, Tuple

from openai import OpenAI

from app.config import settings

log = logging.getLogger(__name__)

# Cheap, and markedly better than gpt-3.5-turbo at reading reporting for whether a
# policy step actually happened.
MODEL = "gpt-4o-mini"

AGENDA_CATEGORIES = [
    "Federal Agency Capture",
    "Judicial Defiance",
    "Suppression of Dissent",
    "NATO Disengagement",
    "Media Subversion",
]

# "Unknown" belongs here as well as in the prompt. Without it the model's own
# "Unknown" is rejected as unrecognised and its reasoning thrown away, replacing
# a considered "the excerpts do not cover this" with a parser complaint.
VALID_STATUSES = ["Achieved", "InProgress", "Obstructed", "Not Started", "Unknown"]

# "Not Started" is a claim about the world: nothing has happened yet. A failed API
# call, a missing key, or no coverage are claims about us, and rendering them as
# "Not Started" put confident grey badges on proposals that had visibly already
# happened — the Department of Education teardown and the CPB defunding among
# them. UNKNOWN keeps the two apart.
UNKNOWN = "Unknown"


def get_openai_client() -> Optional[OpenAI]:
    if not settings.openai_api_key:
        return None
    # Rate limits and brief 5xx responses are transient; the SDK retries them with
    # backoff. Without this a single blip marks a proposal unscored until someone
    # notices and re-runs.
    return OpenAI(api_key=settings.openai_api_key, max_retries=3)


def score_prediction_with_reasoning(prediction_text: str, news_summary: str) -> Tuple[str, str]:
    """Return (status, one-line reasoning).

    Reasoning is not decoration: a bare label gives the reader no way to tell
    whether the model actually found evidence or guessed from the headline.
    """
    client = get_openai_client()
    if not client:
        return UNKNOWN, "OpenAI API key not configured"
    if not news_summary:
        return UNKNOWN, "No news coverage found for this proposal"

    prompt = f"""You are assessing whether a specific policy proposal has been acted on,
using only the news excerpts provided.

PROPOSAL: "{prediction_text}"

EVIDENCE:
{news_summary[:6000]}

The evidence may contain two kinds of source, and they do not carry equal weight:
- FEDERAL REGISTER DOCUMENTS are the official record of government action. A
  Presidential Document or a final Rule on point is strong evidence the proposal
  was carried out. A Proposed Rule indicates it is underway.
- NEWS COVERAGE is reporting about events, useful for context and for whether
  something was blocked.

Choose exactly one status:
- "Achieved"    - the proposal has been substantially carried out
- "InProgress"  - concrete steps taken, not complete
- "Obstructed"  - attempted but blocked by courts, Congress, or reversal
- "Not Started" - the excerpts show this proposal has NOT been acted on
- "Unknown"     - the excerpts do not address this proposal either way

Rules:
- Judge ONLY from the excerpts.
- "Unknown" is the DEFAULT. Start there and move off it only when the excerpts
  give you a reason to — but a reason can come from any source present. An
  encyclopedia passage stating that an action occurred, with dates, is a reason.
  Ranking sources decides what to believe when they CONFLICT; it is not a licence
  to ignore the only source that addresses the proposal.
- "Not Started" is a positive claim that this proposal has NOT been acted on, and
  it needs evidence saying so — reporting that it stalled, was abandoned, was
  never introduced. If your reasoning would be "the excerpts do not provide
  evidence", "the excerpts do not address this", or "there is no mention of
  this", the answer is "Unknown", NOT "Not Started". Those sentences describe the
  excerpts, not the world, and publishing them as "Not Started" tells the reader
  something false.
- Absence of evidence is not evidence of obstruction either.
- "Obstructed" requires evidence something actually blocked it, not merely that
  the excerpts mention opposition or criticism.
- Headlines about a related topic are not evidence about THIS proposal.
- A Federal Register document must actually concern THIS proposal. Unrelated rules
  that merely share a word are not evidence.

Respond as JSON only:
{{"status": "<one of the four>", "reason": "<one sentence, under 25 words, citing what in the excerpts led you there>"}}"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system",
                 "content": "You assess policy implementation from news evidence. "
                            "You are careful about what the evidence does and does not show. "
                            "Respond with JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)
        status = str(data.get("status", "")).strip()
        reason = str(data.get("reason", "")).strip()
        if status not in VALID_STATUSES:
            log.warning("Invalid status %r for %r", status, prediction_text[:50])
            return UNKNOWN, f"Model returned an unrecognised status: {status!r}"
        return status, reason or "No reasoning given"
    except Exception as e:
        # The class name alone is undiagnosable from the page. RateLimitError in
        # particular covers both genuine throttling and an exhausted quota, and
        # only the message says which.
        log.error("Scoring failed for %r: %s", prediction_text[:50], e, exc_info=True)
        return UNKNOWN, f"Scoring failed ({type(e).__name__}): {e}"


def score_prediction_status(prediction_text: str, news_summary: str) -> str:
    """Backwards-compatible wrapper returning just the status."""
    return score_prediction_with_reasoning(prediction_text, news_summary)[0]


def assign_tag_with_ai(article_text: str) -> str:
    """Classify an article into one of the agenda categories."""
    client = get_openai_client()
    if not client:
        return "None"

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system",
                 "content": "You classify news into one of these categories: "
                            + ", ".join(AGENDA_CATEGORIES)
                            + ". If none clearly apply, return 'None'. Return only the category name."},
                {"role": "user", "content": f"Classify this article:\n{article_text[:3000]}"},
            ],
            temperature=0.0,
            max_tokens=20,
        )
        tag = response.choices[0].message.content.strip()
        return tag if tag in AGENDA_CATEGORIES else "None"
    except Exception as e:
        log.error("Tagging failed: %s", e)
        return "None"


CATEGORY_DESCRIPTIONS = {
    "Federal Agency Capture": "federal agencies staffed with political loyalists, career staff "
                              "replaced or stripped of protections, agency independence reduced",
    "Judicial Defiance": "the executive branch ignoring, defying, or acting to undermine court "
                         "rulings and judicial independence",
    "Suppression of Dissent": "action to silence critics, restrict protest, target journalists, "
                              "or intimidate political opposition",
    "NATO Disengagement": "reducing NATO commitments, withdrawing forces from allies, or "
                          "realigning away from the alliance",
    "Media Subversion": "defunding or delegitimising independent media, or promoting "
                        "state-aligned narratives",
}


def analyze_category_with_reasoning(category: str, news_summary: str) -> Tuple[Optional[int], str]:
    """Return (percentage 0-100, one-line justification), or (None, why) on failure.

    None means no figure was produced. The caller keeps whatever it already had
    rather than publishing a zero nobody measured.

    The old version asked for a bare number with a scale anchored on loaded terms
    and no requirement to point at anything. A number nobody can interrogate is
    worse than no number, so it now has to say what drove it.
    """
    client = get_openai_client()
    if not client:
        return 0, "OpenAI API key not configured"
    if not news_summary:
        return 0, "No news coverage found for this category"

    description = CATEGORY_DESCRIPTIONS.get(category, category)
    prompt = f"""Assess how far the following has advanced, using only the excerpts provided.

CATEGORY: {category}
DEFINITION: {description}

NEWS EXCERPTS:
{news_summary[:6000]}

Scale:
   0  = no evidence of this in the excerpts
  25  = isolated incidents
  50  = a clear pattern of concrete steps
  75  = extensive, institutionalised change
 100  = essentially complete

Rules:
- Judge ONLY from the excerpts. If they say little about this category, score low
  and say so — do not fill the gap with background knowledge.
- Cite what drove the number.

Respond as JSON only:
{{"score": <integer 0-100>, "reason": "<one sentence, under 25 words>"}}"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system",
                 "content": "You assess political developments from news evidence, "
                            "carefully and without overreaching. Respond with JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content.strip())
        score = int(re.sub(r"[^0-9]", "", str(data.get("score", 0))) or 0)
        return max(0, min(100, score)), str(data.get("reason", "")).strip() or "No reasoning given"
    except Exception as e:
        # None, not 0 — a zeroed bar is a measurement, and this is the absence of
        # one. The caller keeps whatever it had rather than publishing a figure
        # nobody computed.
        log.error("Category analysis failed for %s: %s", category, e, exc_info=True)
        return None, f"Analysis failed ({type(e).__name__}): {e}"


def analyze_category_progress(category: str, news_summary: str) -> int:
    """Backwards-compatible wrapper returning just the percentage."""
    return analyze_category_with_reasoning(category, news_summary)[0]
