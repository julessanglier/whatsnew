# whatsnew — Daily Tech Watch

[![Daily Tech Watch](https://github.com/julessanglier/whatsnew/actions/workflows/daily_report.yml/badge.svg)](https://github.com/julessanglier/whatsnew/actions/workflows/daily_report.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)

Automated daily trending tech report. Runs every morning at 07:00 UTC via GitHub Actions, scrapes GitHub Trending, Product Hunt, Skills.sh, enriches with Claude AI, and commits a Markdown report.

## Latest Report

[**View latest report →**](https://github.com/julessanglier/whatsnew/blob/main/reports/latest.md)

## Sources

| Source | What it fetches | Credentials required |
|--------|----------------|----------------------|
| GitHub Trending | Top repos trending today | None |
| Product Hunt | Top products of the day | `PRODUCTHUNT_API_KEY` (optional, falls back to scraping) |
| Skills.sh | Trending developer skills | None |

## Sample Output

```markdown
# whatsnew ☕ — 2026-03-15
*Generated on 2026-03-15 07:00 UTC*

## Summary
Today's highlights lean heavily toward AI tooling and Rust-based developer utilities...

## GitHub Trending
- **[burn-rs / burn](https://github.com/burn-rs/burn)** `Rust` — ⭐ 312
  *Deep learning framework built for flexibility and performance*
  > Why it's trending: New v0.14 release with WGPU backend improvements
  > Relevance: Rust + ML tooling matches your core interests

## Product Hunt
- **[Cursor 0.40](https://www.producthunt.com/posts/cursor-0-40)**
  *AI code editor with multi-file edit and background agents*
  > Relevance: Developer productivity tool, directly in your wheelhouse
```

## Reports

- [`reports/latest.md`](reports/latest.md) — most recent report
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
