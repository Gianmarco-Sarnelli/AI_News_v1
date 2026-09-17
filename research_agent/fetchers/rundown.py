"""Fetches and parses the Rundown AI newsletter RSS feed.

The feed is public (no auth), served via Beehiiv:
https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml

Each RSS <item> is one full daily issue, with several individual stories
embedded as HTML inside <content:encoded>. This module splits an issue
apart into individual NewsItems -- one per story -- so the agent ranks
and summarizes stories, not whole issues.

Note: this parses Beehiiv's current HTML structure (each story lives in
a `<div class="section">` with an `<h6>` category label and an `<h4>`
headline). If Rundown/Beehiiv changes their template, `_extract_stories`
is the only function that needs updating.
"""
from __future__ import annotations

import datetime as dt
import re

import feedparser
from bs4 import BeautifulSoup

from research_agent.config import RUNDOWN_RSS_URL
from research_agent.models import NewsItem

# Section labels that mark sponsored content -- skip these, they aren't news.
_AD_MARKERS = ("PRESENTED BY", "TOGETHER WITH", "SPONSORED")

# Rundown headlines are prefixed with an emoji (e.g. "😳 Anthropic opens...").
# Strip it once the title is plain text.
_LEADING_EMOJI_RE = re.compile(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\s]+")


def _clean_title(raw_title: str) -> str:
    return _LEADING_EMOJI_RE.sub("", raw_title).strip()


def _extract_stories(
    issue_html: str, issue_title: str, published_at: dt.datetime | None
) -> list[NewsItem]:
    soup = BeautifulSoup(issue_html, "html.parser")
    stories: list[NewsItem] = []

    for section in soup.find_all("div", class_="section"):
        h6 = section.find("h6")
        h4 = section.find("h4")
        if h4 is None:
            continue  # not a story block (e.g. the black "LATEST DEVELOPMENTS" divider)

        category = h6.get_text(strip=True) if h6 else ""
        if any(marker in category.upper() for marker in _AD_MARKERS):
            continue  # skip sponsored sections

        link_tag = h4.find("a")
        title = _clean_title(h4.get_text(strip=True))
        url = link_tag["href"] if link_tag else None
        if not title or not url:
            continue

        paragraphs = [
            p.get_text(strip=True) for p in section.find_all("p") if p.get_text(strip=True)
        ]
        summary = " ".join(paragraphs)

        stories.append(
            NewsItem(
                title=title,
                url=url,
                summary=summary,
                source="rundown_ai",
                published_at=published_at,
                category=category.title(),
                metrics={"issue_title": issue_title},
            )
        )
    return stories


def fetch_latest_stories(num_issues: int = 1) -> list[NewsItem]:
    """Fetch and flatten stories from the most recent `num_issues` newsletter issues."""
    feed = feedparser.parse(RUNDOWN_RSS_URL)
    if feed.bozo and not feed.entries:
        raise RuntimeError(f"Failed to parse Rundown AI RSS feed: {feed.bozo_exception}")

    all_stories: list[NewsItem] = []
    for entry in feed.entries[:num_issues]:
        if "content" in entry and entry.content:
            issue_html = entry.content[0].value
        else:
            issue_html = entry.get("summary", "")

        published_at = None
        if entry.get("published_parsed"):
            published_at = dt.datetime(*entry.published_parsed[:6], tzinfo=dt.timezone.utc)

        all_stories.extend(_extract_stories(issue_html, entry.title, published_at))

    return all_stories


if __name__ == "__main__":
    # Quick manual check: `python -m research_agent.fetchers.rundown`
    stories = fetch_latest_stories()
    print(f"Fetched {len(stories)} stories\n")
    for s in stories:
        print(f"[{s.category}] {s.title}")
        print(f"  {s.url}")
