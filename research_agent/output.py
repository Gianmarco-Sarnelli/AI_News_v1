"""Renders curated items into a Markdown digest file."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from research_agent.agent import CuratedItem

OUTPUT_DIR = Path(__file__).parent.parent / "digests"

_RELEVANCE_EMOJI = {"high": "\U0001F534", "medium": "\U0001F7E1", "low": "\u26AA"}


def render_markdown(curated: list[CuratedItem], profile: str) -> str:
    today = dt.date.today().isoformat()
    lines = [f"# AI Research Digest — {today}", ""]

    if not curated:
        lines.append("_No new items today._")
        return "\n".join(lines)

    has_deep_dives = any(c.deep_dive for c in curated)
    if has_deep_dives:
        lines.append("## \U0001F50E Deep Dives")
        lines.append("")
        for c in curated:
            if not c.deep_dive:
                continue
            lines.append(f"### {c.item.title}")
            lines.append(f"*{c.item.source} · [{c.item.url}]({c.item.url})*")
            lines.append("")
            lines.append(c.deep_dive)
            lines.append("")

    lines.append("## \U0001F4CB Today's Items")
    lines.append("")
    for c in curated:
        emoji = _RELEVANCE_EMOJI.get(c.relevance, "\u26AA")
        lines.append(f"- {emoji} **[{c.item.title}]({c.item.url})** — {c.why_it_matters}")

    lines.append("")
    lines.append("---")
    lines.append(f"_Current interest profile: {profile}_")

    return "\n".join(lines)


def write_digest(curated: list[CuratedItem], profile: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{dt.date.today().isoformat()}.md"
    path.write_text(render_markdown(curated, profile))
    return path
