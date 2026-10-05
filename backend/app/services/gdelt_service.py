"""GDELT lookups — news coverage older than NewsAPI's free tier can reach.

NewsAPI's free tier searches roughly the last month. Policy actions taken early in
the administration therefore had no findable coverage, and the Federal Register
only helps when the action took the form of a rule or an executive order. The
Department of Education teardown is neither: it runs through interagency
agreements moving programs to Justice, HHS and Labor, reported in the press and
absent from the Register. That evidence existed and the tracker could not see it.

GDELT indexes global news back years, needs no API key, and is free.

Two properties shape how this is used:

  Rate limit. One request every five seconds. Calling it for all 21 proposals plus
  five categories would add over two minutes to a blocking re-score, so callers
  should ask only when better evidence is missing.

  Titles only. The article list carries no snippet or description, so a result is
  a headline, a date and a domain. That is weaker than a Federal Register document
  and is labelled as such for the scoring model, which otherwise has no way to
  know it is reading a headline rather than a record of government action.
"""
import json
import logging
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Tuple

log = logging.getLogger(__name__)

BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
_UA = {"User-Agent": "Project2025Watch/1.0 (policy tracker)"}

# GDELT asks for one request every five seconds and returns a plain-text scolding
# rather than JSON when that is exceeded — which parses as "no coverage found" and
# would quietly look like an answer.
_MIN_INTERVAL = 5.0
_last_call = 0.0


def _throttle() -> None:
    global _last_call
    wait = _MIN_INTERVAL - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.monotonic()


def search(query: str, max_records: int = 6,
           since: str = "20250120000000") -> List[Dict]:
    """Articles matching `query`, newest first. Empty list on any failure.

    `since` defaults to the start of the administration, matching the window the
    Federal Register lookups use.
    """
    if not query:
        return []
    params = {
        "query": f"{query} sourcelang:eng",
        "mode": "artlist",
        "maxrecords": max_records,
        "format": "json",
        "startdatetime": since,
        "sort": "datedesc",
    }
    url = BASE + "?" + urllib.parse.urlencode(params)
    body = ""
    # The throttle only knows about calls this process made. A 429 means something
    # else shared the budget, and backing off recovers rather than reporting the
    # proposal as uncovered.
    for attempt in range(3):
        _throttle()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=30) as r:
                body = r.read().decode("utf-8", "replace")
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                log.info("GDELT rate limited, backing off (attempt %d)", attempt + 1)
                time.sleep(_MIN_INTERVAL * (attempt + 2))
                continue
            log.warning("GDELT lookup failed for %r: %s", query[:60], e)
            return []
        except Exception as e:
            log.warning("GDELT lookup failed for %r: %s", query[:60], e)
            return []
    if not body:
        return []
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        # Over the rate limit, or a malformed query. GDELT answers in prose.
        log.warning("GDELT returned non-JSON for %r: %s", query[:60], body[:120])
        return []

    out = []
    for a in data.get("articles") or []:
        seen = (a.get("seendate") or "")[:8]
        out.append({
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "date": f"{seen[:4]}-{seen[4:6]}-{seen[6:8]}" if len(seen) == 8 else "",
            "domain": a.get("domain", ""),
        })
    return out


def summarise_for_scoring(articles: List[Dict]) -> str:
    """Render articles as evidence text, labelled for what they are.

    Marked as headlines so the scoring model weighs them below a Federal Register
    document. A headline is evidence that something was reported, which is not the
    same as the official record of it happening.
    """
    if not articles:
        return ""
    lines = ["NEWS HEADLINES (reporting, weaker evidence than the Federal Register; "
             "headline and date only, no article text):"]
    for a in articles:
        lines.append(f"- {a['date']} ({a['domain']}) {a['title']}")
    return "\n".join(lines)


def links_for(articles: List[Dict], limit: int = 3) -> List[Dict]:
    return [{"title": a["title"][:110], "url": a["url"]}
            for a in articles[:limit] if a.get("url")]


def search_with_links(query: str, max_records: int = 6) -> Tuple[str, List[Dict]]:
    arts = search(query, max_records=max_records)
    return summarise_for_scoring(arts), links_for(arts)
