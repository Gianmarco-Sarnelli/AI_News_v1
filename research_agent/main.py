"""Entry point: run the full daily pipeline end to end.

    python -m research_agent.main
"""
from __future__ import annotations

from research_agent.agent import curate
from research_agent.openrouter_client import get_key_usage
from research_agent.output import write_digest
from research_agent.pipeline import gather_items
from research_agent.profile import load_profile, update_profile_from_feedback


def run() -> None:
    profile = load_profile()
    print(f"Interest profile: {profile}\n")

    print("Fetching sources...")
    items = gather_items()
    print(f"Found {len(items)} new items.\n")

    if not items:
        print("Nothing new today — skipping curation.")
        return

    print("Curating with the agent (this calls OpenRouter)...")
    curated = curate(items, profile)

    path = write_digest(curated, profile)
    print(f"\nDigest written to {path}\n")

    try:
        usage = get_key_usage()
        remaining = usage.get("limit_remaining")
        spent = usage.get("usage", 0)
        remaining_str = f", ${remaining:.4f} remaining" if remaining is not None else ", no hard limit set"
        print(f"OpenRouter usage: ${spent:.4f} spent{remaining_str}")
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] Could not fetch OpenRouter usage: {exc}")

    digest_titles = "\n".join(f"- {c.item.title}" for c in curated)
    feedback = input("\nAny feedback on today's digest? (blank to skip): ").strip()
    if feedback:
        new_profile = update_profile_from_feedback(profile, digest_titles, feedback)
        print(f"\nUpdated interest profile:\n{new_profile}")


if __name__ == "__main__":
    run()
