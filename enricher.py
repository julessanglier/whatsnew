"""
Claude AI enrichment for the daily tech watch report.
If ANTHROPIC_API_KEY is not set, all functions return the input unchanged.
"""
from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from sources.base import TrendingItem

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            return None
        try:
            import anthropic
            _client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            return None
    return _client


def _load_profile() -> str:
    profile_path = Path("profile.md")
    if profile_path.exists():
        return profile_path.read_text(encoding="utf-8")
    return ""


def filter_and_rank(
    items_by_source: dict[str, list[TrendingItem]],
) -> dict[str, list[TrendingItem]]:
    """Filter and rank items by relevance to user profile using Claude."""
    client = _get_client()
    if not client:
        return items_by_source

    profile = _load_profile()
    if not profile:
        return items_by_source

    # Build flat list with source tags
    flat_items = []
    for source_name, items in items_by_source.items():
        for i, item in enumerate(items):
            flat_items.append(f"[{source_name}][{i}] {item.title}: {item.description or ''}")

    if not flat_items:
        return items_by_source

    prompt = f"""Given this user interest profile:

{profile}

Here are today's trending items:
{chr(10).join(flat_items)}

Return a JSON array of objects with fields:
- source: the source name in brackets
- index: the integer index in brackets
- relevance_score: 1-10
- reason: one short sentence why it matches interests

Only include items with relevance_score >= 6. Sort by score descending.
Return only the JSON array, no other text."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        text = message.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        ranked = json.loads(text)

        # Rebuild items_by_source preserving only relevant items
        result: dict[str, list[TrendingItem]] = {k: [] for k in items_by_source}
        for entry in ranked:
            source = entry["source"]
            idx = int(entry["index"])
            reason = entry.get("reason", "")
            if source in items_by_source and idx < len(items_by_source[source]):
                item = items_by_source[source][idx]
                item.extra["relevance_reason"] = reason
                item.extra["relevance_score"] = entry.get("relevance_score", 0)
                result[source].append(item)

        return result
    except Exception:
        return items_by_source


def annotate_items(items_by_source: dict[str, list[TrendingItem]]) -> dict[str, list[TrendingItem]]:
    """Add 'why it's trending' annotation to each item."""
    client = _get_client()
    if not client:
        return items_by_source

    flat_items = []
    index_map = []
    for source_name, items in items_by_source.items():
        for i, item in enumerate(items):
            flat_items.append(f"[{source_name}][{i}] {item.title}: {item.description or ''}")
            index_map.append((source_name, i))

    if not flat_items:
        return items_by_source

    prompt = f"""For each of these trending tech items, write one sentence explaining what it does and why it's notable or trending today:

{chr(10).join(flat_items)}

Return a JSON array where each element has:
- source: source name
- index: integer index
- annotation: one-sentence explanation

Return only the JSON array."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        text = message.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        annotations = json.loads(text)

        for entry in annotations:
            source = entry["source"]
            idx = int(entry["index"])
            annotation = entry.get("annotation", "")
            if source in items_by_source and idx < len(items_by_source[source]):
                items_by_source[source][idx].extra["annotation"] = annotation

    except Exception:
        pass

    return items_by_source


def generate_summary(items_by_source: dict[str, list[TrendingItem]]) -> Optional[str]:
    """Generate a 3-5 bullet executive summary of the day's themes."""
    client = _get_client()
    if not client:
        return None

    flat_items = []
    for source_name, items in items_by_source.items():
        for item in items:
            flat_items.append(f"- [{source_name}] {item.title}: {item.description or ''}")

    if not flat_items:
        return None

    prompt = f"""Based on today's trending tech items:

{chr(10).join(flat_items)}

Write a 3-5 bullet TL;DR summary highlighting the day's big themes.
Start each bullet with an emoji. Be concise and insightful.
Return only the bullet points, no header."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception:
        return None


def generate_weekly_digest(reports_dir: Path, today: date) -> Optional[str]:
    """Generate a weekly digest on Mondays by reading the past 7 daily reports."""
    if today.weekday() != 0:  # 0 = Monday
        return None

    client = _get_client()
    if not client:
        return None

    # Collect past 7 days of reports
    reports_content = []
    for i in range(1, 8):
        d = today - timedelta(days=i)
        report_path = reports_dir / f"{d.isoformat()}.md"
        if report_path.exists():
            reports_content.append(f"### {d.isoformat()}\n{report_path.read_text(encoding='utf-8')}")

    if not reports_content:
        return None

    combined = "\n\n---\n\n".join(reports_content)

    prompt = f"""Here are the tech watch reports from the past week:

{combined}

Write a weekly digest that:
1. Identifies cross-week themes and trends
2. Highlights the most impactful projects/launches
3. Notes any recurring topics or growing momentum
4. Provides a 1-paragraph outlook

Use clear Markdown with sections. Be analytical and concise."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception:
        return None
