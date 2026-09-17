"""Manages the user's interest profile and updates it from daily
feedback. The profile is a short natural-language description injected
into the agent's curation prompt -- not a keyword/weight list -- so it
can capture nuance ("more of X, but only technical deep-dives, not
news coverage of X") that a tag system can't.
"""
from __future__ import annotations

import json
from pathlib import Path

from research_agent.openrouter_client import chat_completion

PROFILE_PATH = Path(__file__).parent.parent / "data" / "profile.json"

DEFAULT_PROFILE = (
    "No strong preferences yet. Surface a broad mix of significant AI "
    "research and news, weighted toward technical depth over hype."
)

_UPDATE_SYSTEM_PROMPT = """You maintain a short interest profile for a daily AI \
news digest. You will be given the current profile, the items shown in today's \
digest, and the user's feedback on it. Rewrite the profile to incorporate the \
feedback.

Rules:
- Keep it under 150 words, plain prose, not bullet points.
- Preserve existing preferences the feedback doesn't contradict.
- Be specific ("less coverage of funding/valuation news" beats "less business news").
- If the feedback is vague or emotional, use your judgment on what it implies \
rather than ignoring it.
- Respond with ONLY the new profile text -- no preamble, no quotes, no markdown."""


def load_profile() -> str:
    if not PROFILE_PATH.exists():
        return DEFAULT_PROFILE
    data = json.loads(PROFILE_PATH.read_text())
    return data.get("profile", DEFAULT_PROFILE)


def save_profile(profile_text: str) -> None:
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.write_text(json.dumps({"profile": profile_text.strip()}, indent=2))


def update_profile_from_feedback(
    current_profile: str,
    digest_summary: str,
    feedback: str,
    model: str | None = None,
) -> str:
    """Rewrite the profile given today's feedback, persist it, and return the new text."""
    if not feedback.strip():
        return current_profile

    user_prompt = (
        f"CURRENT PROFILE:\n{current_profile}\n\n"
        f"TODAY'S DIGEST (titles shown):\n{digest_summary}\n\n"
        f"USER FEEDBACK:\n{feedback}"
    )

    new_profile = chat_completion(
        messages=[
            {"role": "system", "content": _UPDATE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        max_tokens=300,
        temperature=0.3,
    ).strip()

    save_profile(new_profile)
    return new_profile
