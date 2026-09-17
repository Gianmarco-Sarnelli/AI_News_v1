"""Lightweight SQLite-backed dedup store. Keeps a record of every item
URL the agent has already surfaced, so re-running on the same day, or a
story showing up again in a later pull, doesn't produce duplicate
digest entries.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from research_agent.models import NewsItem

DB_PATH = Path(__file__).parent.parent / "data" / "history.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_items (
            url TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            first_seen TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    return conn


def filter_unseen(items: list[NewsItem]) -> list[NewsItem]:
    """Return only the items whose URL hasn't been recorded before."""
    conn = _connect()
    try:
        seen_urls = {row[0] for row in conn.execute("SELECT url FROM seen_items")}
    finally:
        conn.close()
    return [item for item in items if item.url not in seen_urls]


def mark_seen(items: list[NewsItem]) -> None:
    conn = _connect()
    try:
        conn.executemany(
            "INSERT OR IGNORE INTO seen_items (url, source, title) VALUES (?, ?, ?)",
            [(item.url, item.source, item.title) for item in items],
        )
        conn.commit()
    finally:
        conn.close()
