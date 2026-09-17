"""Central configuration for the research agent.

All settings are read from environment variables (via a local .env file,
see .env.example). Nothing here should ever contain a real key -- copy
.env.example to .env and fill it in locally.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# --- Emergent Mind (arXiv papers) -------------------------------------------
# Free key: https://www.emergentmind.com/api-keys (50 requests/month on Free)
EMERGENT_MIND_API_KEY = os.environ.get("EMERGENT_MIND_API_KEY", "")

# --- Rundown AI (general AI news, via public RSS) ---------------------------
RUNDOWN_RSS_URL = os.environ.get(
    "RUNDOWN_RSS_URL",
    "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml",
)

# --- OpenRouter (model provider) --------------------------------------------
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# Any OpenRouter model slug works here, e.g. "anthropic/claude-opus-5".
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-5")
