"""Core agent step: filter, rank, and deep-dive the day's items in one
LLM call via OpenRouter.

Given every fetched item plus the user's current interest profile, the
model decides what's worth surfacing, writes a one-line "why this
matters" for each, and independently chooses between 1 and 3 items to
analyze in depth -- its own judgment call on what's most insightful,
not necessarily the items ranked highest for the user's stated
interests.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from research_agent.models import NewsItem
from research_agent.openrouter_client import chat_completion

_SYSTEM_PROMPT = """You are a research assistant curating a daily AI digest for a \
data scientist who wants to stay current on AI research and news. You will be \
given the user's current interest profile and a numbered list of today's items \
(arXiv papers and AI news stories).

Your job:
- Decide which items are worth surfacing at all. Drop items that are clearly \
irrelevant to AI/ML or purely promotional/sponsored.
- For every item you keep, write ONE short sentence ("why_it_matters") explaining \
its relevance -- specific, not generic hype.
- Assign a relevance tier: "high", "medium", or "low", based on fit with the \
user's stated interests AND general significance to the field.
- From ALL kept items, choose between 1 and 3 that you judge to be the most \
genuinely insightful or significant today -- use your own judgment about what \
an informed AI practitioner would most want to understand deeply, not just \
whichever items scored "high" relevance. For each chosen item, write a \
substantive "deep_dive" analysis (150-300 words): what it actually does or \
claims, why it matters, how it connects to recent trends or open questions, and \
any caveats or reasons for skepticism. Do not pad -- every sentence should carry \
information.

Respond with ONLY valid JSON, no markdown code fences, no commentary, matching \
exactly this shape:

{
  "kept_items": [
    {"index": <int>, "relevance": "high"|"medium"|"low", "why_it_matters": "<string>"}
  ],
  "deep_dives": [
    {"index": <int>, "analysis": "<string>"}
  ]
}

"index" refers to the item's position in the list you were given (0-based). \
deep_dives must reference indices that also appear in kept_items, and must \
contain between 1 and 3 entries."""


@dataclass
class CuratedItem:
    item: NewsItem
    relevance: str
    why_it_matters: str
    deep_dive: str | None = None


def _format_items_for_prompt(items: list[NewsItem]) -> str:
    lines = []
    for i, item in enumerate(items):
        lines.append(
            f"[{i}] SOURCE: {item.source} | CATEGORY: {item.category}\n"
            f"TITLE: {item.title}\n"
            f"SUMMARY: {item.summary[:800]}\n"
            f"URL: {item.url}"
        )
    return "\n\n".join(lines)


def _parse_json_response(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    return json.loads(cleaned.strip())


def curate(items: list[NewsItem], profile: str, model: str | None = None) -> list[CuratedItem]:
    """Filter, rank, and deep-dive today's items in a single LLM call."""
    if not items:
        return []

    user_prompt = (
        f"INTEREST PROFILE:\n{profile}\n\n"
        f"TODAY'S ITEMS ({len(items)} total):\n\n"
        f"{_format_items_for_prompt(items)}"
    )

    raw = chat_completion(
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
    )

    try:
        parsed = _parse_json_response(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Agent did not return valid JSON. Raw response:\n{raw}") from exc

    deep_dive_map = {d["index"]: d["analysis"] for d in parsed.get("deep_dives", [])}

    curated: list[CuratedItem] = []
    for kept in parsed.get("kept_items", []):
        idx = kept.get("index")
        if not isinstance(idx, int) or idx < 0 or idx >= len(items):
            continue  # ignore hallucinated/out-of-range indices rather than crash
        curated.append(
            CuratedItem(
                item=items[idx],
                relevance=kept.get("relevance", "medium"),
                why_it_matters=kept.get("why_it_matters", ""),
                deep_dive=deep_dive_map.get(idx),
            )
        )
    return curated
