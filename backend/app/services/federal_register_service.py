"""Federal Register lookups — the primary record of whether a policy actually happened.

NewsAPI's free tier only searches roughly the last month, so a proposal enacted in
early 2025 had no findable coverage and scored "Not Started" forever. That is a
data problem, not a scoring problem: the tracker was asking the wrong source.

Project 2025 proposals are implemented through executive orders, proposed rules and
final rules, and every one of those is published in the Federal Register. Its API is
free, needs no key, and goes back decades. A Federal Register document is also
stronger evidence than reporting — it is not an article about the action, it IS the
action.

Query syntax matters: a bare term is full-text and far too loose ("Schedule Policy
Career" returns 2,843 documents including Medicare rules), while the quoted phrase
returns 9, led by the executive order itself.
"""
import json
import logging
import urllib.parse
import urllib.request
from typing import Dict, List, Tuple

log = logging.getLogger(__name__)

BASE = "https://www.federalregister.gov/api/v1/documents.json"
_UA = {"User-Agent": "Project2025Watch/1.0 (policy tracker)"}

# Document types that represent action, roughly strongest first. A final Rule or a
# Presidential Document is evidence something happened; a Proposed Rule is evidence
# something is underway.
ACTION_WEIGHT = {
    "Presidential Document": "enacted",
    "Rule": "enacted",
    "Proposed Rule": "in progress",
    "Notice": "in progress",
}


def search_documents(query: str, per_page: int = 5,
                     since: str = "2025-01-20") -> List[Dict]:
    """Federal Register documents matching `query`, best match first.

    `since` defaults to the start of the administration, so results are scoped to
    the period the tracker covers rather than returning decades of history.
    """
    if not query:
        return []
    params = {
        "conditions[term]": query,
        "conditions[publication_date][gte]": since,
        "per_page": per_page,
        "order": "relevance",
    }
    url = (BASE + "?" + urllib.parse.urlencode(params)
           + "&fields[]=title&fields[]=publication_date&fields[]=type"
             "&fields[]=html_url&fields[]=abstract&fields[]=agencies")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=30) as r:
            data = json.load(r)
    except Exception as e:
        log.error("Federal Register lookup failed for %r: %s", query[:60], e)
        return []

    out = []
    for doc in data.get("results") or []:
        out.append({
            "title": doc.get("title", ""),
            "date": doc.get("publication_date", ""),
            "type": doc.get("type", ""),
            "url": doc.get("html_url", ""),
            "abstract": (doc.get("abstract") or "")[:400],
        })
    return out


def summarise_for_scoring(docs: List[Dict]) -> str:
    """Render documents as evidence text for the scoring model."""
    if not docs:
        return ""
    lines = ["FEDERAL REGISTER DOCUMENTS (official record of government action):"]
    for d in docs:
        weight = ACTION_WEIGHT.get(d["type"], "")
        marker = f" [{d['type']}" + (f" — {weight}]" if weight else "]")
        lines.append(f"- {d['date']}{marker} {d['title']}")
        if d.get("abstract"):
            lines.append(f"    {d['abstract'][:220]}")
    return "\n".join(lines)


def links_for(docs: List[Dict], limit: int = 3) -> List[Dict]:
    """Article-link shaped records, so Federal Register docs render alongside news."""
    return [{"title": f"[Federal Register {d['date']}] {d['title'][:110]}",
             "url": d["url"]}
            for d in docs[:limit] if d.get("url")]


def search_with_links(query: str, per_page: int = 5) -> Tuple[str, List[Dict]]:
    """Convenience: (evidence text, link records)."""
    docs = search_documents(query, per_page=per_page)
    return summarise_for_scoring(docs), links_for(docs)
