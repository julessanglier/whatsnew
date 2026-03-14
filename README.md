# whatsnew — Daily Tech Watch

Automated daily trending tech report. Runs every morning at 07:00 UTC via GitHub Actions, scrapes GitHub Trending, Product Hunt, Skills.sh, enriches with Claude AI, and commits a Markdown report.

## Reports

- `reports/latest.md` — most recent report
- `reports/YYYY-MM-DD.md` — daily archives
- `reports/weekly-YYYY-WXX.md` — weekly digests (Mondays)

## Setup

1. **Fork/clone** this repo
2. **Add secrets** in repo Settings → Secrets and variables → Actions:
   - `ANTHROPIC_API_KEY` — for Claude AI enrichment (optional but recommended)
   - `PRODUCTHUNT_API_KEY` — for Product Hunt API (optional, falls back to scraping)
3. **Edit `profile.md`** to describe your interests — Claude uses this to filter and rank items
4. **Run manually** via Actions tab → Daily Tech Watch → Run workflow

## Local Development

```bash
uv sync
cp .env.example .env  # add your API keys
uv run python generate_report.py
```

## Adding a New Source

Create `sources/my_source.py`:

```python
from sources.base import BaseSource, TrendingItem

class MySource(BaseSource):
    name = "My Source"

    def fetch(self) -> list[TrendingItem]:
        # scrape or call API
        return [TrendingItem(title="...", url="...")]
```

That's it — zero registration needed. The source is auto-discovered on next run.

## Roadmap

- [ ] **X.com source** — fetch trending posts from curated tech communities (lists, hashtags like `#buildinpublic`, `#ai`, `#devtools`) using the Twitter API v2 Bearer token (`TWITTER_BEARER_TOKEN` secret), with a Nitter-based scraping fallback for no-credentials setups
- [ ] **RSS/Atom source** — generic feed reader configured via an `## RSS Feeds` section in `profile.md` (one URL per line); supports RSS 2.0 and Atom, caps at 10 items per feed, skips broken feeds gracefully

## Architecture

- `sources/` — pluggable source modules (auto-discovered)
- `enricher.py` — Claude AI filtering, annotation, and summarization
- `generate_report.py` — orchestrator
- `profile.md` — your interest profile (edit this!)
- `.github/workflows/daily_report.yml` — daily cron job
