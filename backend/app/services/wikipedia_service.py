"""Wikipedia lookups — background on whether a policy action actually happened.

This exists because GDELT did not work out. GDELT indexes news back years, which
is what the tracker needs, but it allows one request every five seconds and
answers 429 well inside that budget in practice. It also returns headlines with
no article text, so even a successful lookup gave the scoring model a title and a
date to reason from.

Wikipedia is free, needs no key, imposes no rate limit worth engineering around,
and carries prose rather than headlines. More to the point it covers exactly the
actions that were failing to score:

  "The Rescissions Act of 2025 ... rescinds $1.1 billion in funding from the
   Corporation for Public Broadcasting"

  "on March 20, Trump signed an executive order directing the secretary of
   education to 'facilitate the closure' of the department"

Both settle a proposal the Federal Register could not, because neither action
took the form of a rule the Register publishes — one was legislation, the other
reported administrative action.

The obvious caution is that Wikipedia is an encyclopedia, not a primary record.
It is labelled that way for the scoring model, which already ranks the Federal
Register above news, so background reading sits below both.
"""
import json
import logging
import urllib.parse
import urllib.request
from typing import Dict, List, Tuple

log = logging.getLogger(__name__)

API = "https://en.wikipedia.org/w/api.php"
# Wikipedia asks clients to identify themselves and will throttle anonymous
# default agents.
_UA = {"User-Agent": "Project2025Watch/1.0 (policy tracker; contact via GitHub)"}

_EXTRACT_CHARS = 1500


def _get(params: Dict) -> Dict:
    params = {**params, "format": "json"}
    url = API + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=20) as r:
            return json.load(r)
    except Exception as e:
        log.warning("Wikipedia request failed (%s): %s", params.get("srsearch") or params.get("titles"), e)
        return {}


def search_titles(query: str, limit: int = 2) -> List[str]:
    """Article titles matching `query`, best match first."""
    if not query:
        return []
    data = _get({"action": "query", "list": "search", "srsearch": query, "srlimit": limit})
    return [r["title"] for r in data.get("query", {}).get("search", []) if r.get("title")]


def intro_extract(title: str, chars: int = _EXTRACT_CHARS) -> str:
    """Plain-text introduction of an article.

    The introduction rather than the whole article: a Wikipedia lead summarises
    what happened and when, which is the question here, while full articles run to
    tens of thousands of characters and would crowd out the Federal Register text
    in the same prompt.
    """
    data = _get({"action": "query", "prop": "extracts", "explaintext": 1,
                 "exintro": 1, "titles": title, "redirects": 1})
    for page in (data.get("query", {}).get("pages") or {}).values():
        text = (page.get("extract") or "").strip()
        if text:
            return text[:chars]
    return ""


def search_with_links(query: str, limit: int = 2) -> Tuple[str, List[Dict]]:
    """(evidence text, link records) for the best-matching articles."""
    titles = search_titles(query, limit=limit)
    if not titles:
        return "", []
    lines = ["BACKGROUND (encyclopedia summary — not a primary record; weigh below "
             "the Federal Register and contemporaneous reporting):"]
    links = []
    for t in titles:
        extract = intro_extract(t)
        if not extract:
            continue
        lines.append(f"- {t}: {extract}")
        links.append({
            "title": f"[Wikipedia] {t}"[:110],
            "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(t.replace(" ", "_")),
        })
    if not links:
        return "", []
    return "\n".join(lines), links
