"""Wikipedia lookups — background on whether a policy action actually happened.

This exists because GDELT did not work out. GDELT indexes news back years, which
is what the tracker needs, but it allows one request every five seconds and
answers 429 well inside that budget in practice. It also returns headlines with
no article text, so even a successful lookup gave the scoring model a title and a
date to reason from.

Wikipedia is free, needs no key, and carries prose rather than headlines. More to
the point it covers exactly the actions that were failing to score:

  "Trump signed an executive order on March 20, 2025 aimed at closing the
   department to the maximum extent allowed by law"

  "the CPB announced on August 1, 2025, that it would cease operations sometime
   in January 2026"

Both settle a proposal the Federal Register could not, because neither action
took the form of a rule the Register publishes — one was reported administrative
action, the other a funding rescission.

Two things about getting that text out are not obvious, and both cost a full
scoring run before they were fixed.

The lead section is the wrong part of the article. An institution's lead says
what the institution is; the 2025 action sits in a body section. Asking for
`exintro` on "United States Department of Education" returned the department's
staff count and budget, and the scoring model correctly read that as saying
nothing about closing it.

Document order is the wrong way to choose paragraphs. Filtering the body to
paragraphs that mention 2025 or 2026 left sixteen candidates for that article,
and the first few were budget figures that merely happened to carry a year. The
paragraphs are now ranked by how well they match the proposal being scored, so
the executive order beats the appropriations table.

The obvious caution is that Wikipedia is an encyclopedia, not a primary record.
It is labelled that way for the scoring model, which ranks the Federal Register
above it.
"""
import json
import logging
import re
import threading
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Tuple

log = logging.getLogger(__name__)

API = "https://en.wikipedia.org/w/api.php"
# Wikipedia asks clients to identify themselves and throttles anonymous default
# agents.
_UA = {"User-Agent": "Project2025Watch/1.0 (policy tracker; contact via GitHub)"}

_EXTRACT_CHARS = 1800
# Wikipedia answered 429 when a scoring run sent its lookups back to back. One
# request at a time, spaced, with a widening retry — a scoring pass makes a few
# dozen of these and waiting a second between them costs nothing next to the
# model calls it sits between.
_MIN_INTERVAL = 1.5
_BACKOFF = (3, 8, 20)
_lock = threading.Lock()
_last = [0.0]

_YEAR = re.compile(r"\b(2025|2026)\b")
# Words too common in these proposals to carry any signal about which paragraph
# of an article is the relevant one.
_STOP = set("the a an and or of to in for on by with as at from that this its it is are was were be "
            "been being federal united states government department office programs program agency "
            "their his her major other".split())
# A paragraph that reports an action taken counts for more than one that
# describes a proposal, so the verbs of actually doing it are weighted up.
# A wrong article is worse than no article. Searching "Politicization of the
# United States Department of Justice" returned "Supreme Court of the United
# States", and a CCS query returned Norway's offshore carbon tax — handing either
# to the model as evidence about a US proposal is noise it has to see past. An
# article has to actually engage with the proposal's own subject to be used, and
# for the narrower HHS and Endangered Species items nothing on Wikipedia does.
# Those fall back to the Federal Register alone, which is the right source for
# them anyway: unlike a closure by executive order, they take the form of rules
# the Register publishes.
_MIN_RELEVANCE = 4

_ACTION = ("eliminat dismantl abolish closure clos shut terminat rescind repeal revok defund cancel "
           "signed executive order enacted dissolv curtail ended restrict reclassif convert "
           "withdrew withdrawal finalized").split()


def _get(params: Dict) -> Dict:
    params = {**params, "format": "json"}
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=_UA)
    for attempt in range(len(_BACKOFF) + 1):
        with _lock:
            gap = _MIN_INTERVAL - (time.monotonic() - _last[0])
            if gap > 0:
                time.sleep(gap)
            _last[0] = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except Exception as e:
            if attempt >= len(_BACKOFF):
                log.warning("Wikipedia request failed (%s): %s",
                            params.get("srsearch") or params.get("titles"), e)
                return {}
            time.sleep(_BACKOFF[attempt])
    return {}


def search_titles(query: str, limit: int = 2) -> List[str]:
    """Article titles matching `query`, best match first."""
    if not query:
        return []
    data = _get({"action": "query", "list": "search", "srsearch": query, "srlimit": limit})
    return [r["title"] for r in data.get("query", {}).get("search", []) if r.get("title")]


def _article_text(title: str) -> str:
    data = _get({"action": "query", "prop": "extracts", "explaintext": 1,
                 "titles": title, "redirects": 1})
    for page in (data.get("query", {}).get("pages") or {}).values():
        return page.get("extract") or ""
    return ""


def _terms(topic: str) -> set:
    return {w for w in re.findall(r"[a-z]{4,}", topic.lower()) if w not in _STOP}


def _score(paragraph: str, terms: set) -> int:
    low = paragraph.lower()
    return (sum(1 for t in terms if t in low)
            + 2 * sum(1 for a in _ACTION if a in low))


def relevant_extract(title: str, topic: str, chars: int = _EXTRACT_CHARS) -> str:
    """The paragraphs of `title` most likely to say whether `topic` happened.

    Body paragraphs that mention 2025 or 2026, ranked against `topic` and
    returned in document order so the prose still reads. Falls back to the whole
    body when nothing carries a recent year — an article with no 2025 content is
    itself worth the model seeing, since it suggests the action is unrecorded.
    """
    text = _article_text(title)
    if not text:
        return ""
    paragraphs = [p.strip() for p in text.split("\n")
                  if len(p.strip()) > 80 and not p.strip().startswith("=")]
    if not paragraphs:
        return ""
    pool = [p for p in paragraphs if _YEAR.search(p)] or paragraphs
    terms = _terms(topic)
    keep, used = [], 0
    for i in sorted(range(len(pool)), key=lambda i: -_score(pool[i], terms)):
        if used + len(pool[i]) > chars:
            continue
        keep.append(i)
        used += len(pool[i])
        if used > chars * 0.75:
            break
    if not keep:
        return pool[0][:chars]
    return "\n".join(pool[i] for i in sorted(keep))


def search_with_links(query: str, topic: str = "", limit: int = 2) -> Tuple[str, List[Dict]]:
    """(evidence text, link records) for the best-matching articles.

    `topic` is the proposal being scored, and decides which paragraphs of each
    article come back. It defaults to the query only so an exploratory call still
    works; the scoring path always passes the proposal.
    """
    titles = search_titles(query, limit=limit)
    if not titles:
        return "", []
    topic = topic or query
    # The earlier wording — "not a primary record; weigh below the Federal
    # Register" — combined with a prompt that makes Unknown the default, taught
    # the model to discount the only source carrying the answer. Ranking sources
    # was meant to stop a headline outweighing a rule, not to make a dated,
    # sourced account of a completed action count for nothing.
    lines = ["ENCYCLOPEDIA BACKGROUND (secondary source, but a dated and specific "
             "account here is sufficient evidence that something happened):"]
    links = []
    terms = _terms(topic)
    for t in titles:
        extract = relevant_extract(t, topic)
        if not extract:
            continue
        relevance = _score(extract, terms)
        if relevance < _MIN_RELEVANCE:
            log.info("Wikipedia: dropped %r for %r (relevance %d)", t, topic[:40], relevance)
            continue
        lines.append(f"- {t}: {extract}")
        links.append({
            "title": f"[Wikipedia] {t}"[:110],
            "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(t.replace(" ", "_")),
        })
    if not links:
        return "", []
    return "\n".join(lines), links
