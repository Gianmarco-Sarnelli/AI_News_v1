"""Fetch-and-normalize layer: pulls items from every source, filters
out anything seen in a previous run, and returns a flat, ready-to-curate
list. This is the only module that needs to change when a new source
is added.
"""
from __future__ import annotations

from research_agent.fetchers.emergent_mind import fetch_trending_papers
from research_agent.fetchers.rundown import fetch_latest_stories
from research_agent.models import NewsItem
from research_agent.storage import filter_unseen, mark_seen


def gather_items(emergent_mind_results: int = 10, rundown_issues: int = 1) -> list[NewsItem]:
    """Fetch from every source and return only items not seen before.

    Each source is wrapped in its own try/except: one source being down
    (a bad API key, a rate limit, a template change) shouldn't take out
    the whole run.
    """
    items: list[NewsItem] = []

    try:
        items.extend(fetch_trending_papers(num_results=emergent_mind_results))
    except Exception as exc:  # noqa: BLE001 -- intentional catch-all per source
        print(f"[warn] Emergent Mind fetch failed: {exc}")

    try:
        items.extend(fetch_latest_stories(num_issues=rundown_issues))
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] Rundown AI fetch failed: {exc}")

    unseen = filter_unseen(items)
    mark_seen(unseen)
    return unseen
