"""Shared data model. Every fetcher returns a list[NewsItem], regardless
of source, so the rest of the pipeline (ranking, summarizing, output)
never needs to know where an item came from.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NewsItem:
    """A single normalized item: an arXiv paper, a news story, etc."""

    title: str
    url: str
    summary: str
    source: str  # "emergent_mind" | "rundown_ai"
    published_at: Optional[datetime] = None
    category: str = ""  # arXiv category, or Rundown's section label
    authors: list[str] = field(default_factory=list)
    # Source-specific signals (social metrics, related URLs, etc.) -- kept
    # as a free-form dict so each fetcher can attach whatever is useful
    # without forcing a schema change on the others.
    metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "source": self.source,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "category": self.category,
            "authors": self.authors,
            "metrics": self.metrics,
        }
