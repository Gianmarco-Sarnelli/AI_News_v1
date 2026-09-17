# AI Research Digest Agent

A personal daily digest agent that fetches AI papers and news, curates them
with an LLM based on your interests, writes a Markdown summary, and refines
its sense of your interests from your feedback each day.

## What it does

Every run:
1. **Fetches** trending arXiv papers (via the [Emergent Mind](https://www.emergentmind.com) API)
   and today's stories from the [Rundown AI](https://www.therundown.ai) newsletter (via RSS).
2. **Dedupes** against everything it's shown you before (SQLite).
3. **Curates** the remaining items with an LLM (via [OpenRouter](https://openrouter.ai)):
   filters out noise, tags each item's relevance to your interests, and
   independently picks 1–3 items it judges most insightful for a deeper analysis.
4. **Writes** a Markdown digest to `digests/YYYY-MM-DD.md`.
5. **Asks for feedback** and rewrites your interest profile (`data/profile.json`)
   accordingly, so tomorrow's digest adjusts automatically.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Then fill in `.env`:

| Variable | Required | Where to get it |
|---|---|---|
| `EMERGENT_MIND_API_KEY` | Yes | Free tier (50 req/month) at [emergentmind.com/api-keys](https://www.emergentmind.com/api-keys) |
| `OPENROUTER_API_KEY` | Yes | [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys) |
| `OPENROUTER_MODEL` | No | Defaults to `anthropic/claude-sonnet-5`. Any [OpenRouter model slug](https://openrouter.ai/models) works. |
| `RUNDOWN_RSS_URL` | No | Defaults to the public Rundown AI feed. |

## Usage

```bash
python -m research_agent.main
```

This prints progress to the terminal, writes the digest, and prompts you for
feedback at the end. Feel free to skip feedback (just hit enter) on runs
where you have nothing to say — the profile only updates when you give it
something to work with.

### Running the fetchers individually

Useful when debugging a single source without spending an OpenRouter call:

```bash
python -m research_agent.fetchers.rundown
python -m research_agent.fetchers.emergent_mind
python -m research_agent.openrouter_client   # prints your remaining credit
```

## Project structure

```
research_agent/
├── .env.example
├── requirements.txt
├── README.md
└── research_agent/              # the actual package
    ├── config.py                 # loads .env
    ├── models.py                  # shared NewsItem dataclass
    ├── storage.py                   # SQLite dedup store
    ├── pipeline.py                    # fetch + normalize + dedupe both sources
    ├── openrouter_client.py            # chat_completion / get_key_usage / list_models
    ├── agent.py                         # curate(): filter, rank, deep-dive in one call
    ├── profile.py                        # load/save profile.json, feedback-driven rewrite
    ├── output.py                          # renders the Markdown digest
    ├── main.py                             # entry point — run this
    ├── fetchers/
    │   ├── emergent_mind.py
    │   └── rundown.py
    ├── data/                                # profile.json + history.db (created on first run)
    └── digests/                              # daily YYYY-MM-DD.md digests (created on first run)
```

## Notes and known limitations

- **Emergent Mind free tier is 50 requests/month** (~1.6/day). Fine for one
  run/day, but leaves little headroom for repeated testing — lower
  `num_results` in `pipeline.gather_items()` while iterating, rather than
  re-running the full pipeline many times.
- **The Rundown parser depends on Beehiiv's current HTML template.** If
  `fetch_latest_stories()` starts returning zero stories, the newsletter's
  markup likely changed — `_extract_stories()` in `fetchers/rundown.py` is
  the only place that needs updating.
- **The agent's JSON output isn't schema-enforced**, just prompted. If
  `agent.curate()` raises a `JSONDecodeError`, the raw model response is
  included in the error so you can see what went wrong.
- **Nothing here is scheduled yet.** Run it manually, or wire it to cron /
  `launchd` / Task Scheduler for a hands-off daily digest.

## Changing the model

Swap models per-run without touching any other code:

```bash
OPENROUTER_MODEL=anthropic/claude-opus-5 python -m research_agent.main
```

or set it permanently in `.env`.
