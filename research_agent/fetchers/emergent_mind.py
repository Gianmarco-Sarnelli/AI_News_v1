"""Fetches trending arXiv papers from the Emergent Mind API.

Docs: https://www.emergentmind.com/docs/api
Free tier: 50 requests/month -- one call/day fits comfortably.
Get a key at: https://www.emergentmind.com/api-keys
"""
from __future__ import annotations

import datetime as dt

import requests

from research_agent.config import EMERGENT_MIND_API_KEY
from research_agent.models import NewsItem

API_URL = "https://api.emergentmind.com/v1/papers/trending"

# cs.AI / cs.LG / cs.CL cover the bulk of mainstream AI research; add
# categories (e.g. "stat.ML", "cs.CV") if you want a wider net later.
DEFAULT_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL"]


def fetch_trending_papers(
    days_back: int = 1,
    categories: list[str] | None = None,
    num_results: int = 10,
) -> list[NewsItem]:
    """Fetch the top trending arXiv papers from the last `days_back` days.

    Ranking is by accumulated attention (X, Hacker News, Reddit, GitHub,
    YouTube mentions) within the date window, not recency alone -- so a
    paper from two days ago that's still being talked about can outrank
    something published an hour ago.
    """
    if not EMERGENT_MIND_API_KEY:
        raise RuntimeError(
            "EMERGENT_MIND_API_KEY is not set. Get a free key at "
            "https://www.emergentmind.com/api-keys and add it to your .env file."
        )

    start_date = (dt.date.today() - dt.timedelta(days=days_back)).isoformat()
    end_date = dt.date.today().isoformat()

    payload = {
        "start_date": start_date,
        "end_date": end_date,
        "categories": categories or DEFAULT_CATEGORIES,
        "num_results": num_results,
    }
    headers = {
        "x-api-key": EMERGENT_MIND_API_KEY,
        "Content-Type": "application/json",
    }

    response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()

    items: list[NewsItem] = []
    for paper in data.get("results", []):
        published_at = None
        if paper.get("published_at"):
            published_at = dt.datetime.fromisoformat(
                paper["published_at"].replace("Z", "+00:00")
            )

        items.append(
            NewsItem(
                title=paper["title"],
                url=paper.get("emergent_mind_url") or paper["arxiv_abstract_url"],
                summary=paper.get("abstract", ""),
                source="emergent_mind",
                published_at=published_at,
                category=paper.get("primary_category", ""),
                authors=paper.get("authors", []),
                metrics={
                    "twitter_likes": paper.get("twitter_likes_count", 0),
                    "hacker_news_points": paper.get("hacker_news_points_count", 0),
                    "reddit_points": paper.get("reddit_points_count", 0),
                    "github_stars": paper.get("github_stars_count", 0),
                    "citations": paper.get("citations_count", 0),
                    "arxiv_pdf_url": paper.get("arxiv_pdf_url", ""),
                },
            )
        )
    return items


if __name__ == "__main__":
    # Quick manual check: `python -m research_agent.fetchers.emergent_mind`
    papers = fetch_trending_papers()
    print(f"Fetched {len(papers)} trending papers\n")
    for p in papers:
        print(f"- {p.title}")
        print(f"  {p.url}  ({p.metrics['twitter_likes']} X likes, {p.metrics['citations']} citations)")
