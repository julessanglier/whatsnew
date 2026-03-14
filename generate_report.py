#!/usr/bin/env python3
"""
Orchestrator: discovers sources, fetches trending items, enriches with Claude,
writes dated + latest reports to reports/.
"""
from __future__ import annotations

import importlib
import pkgutil
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import sources
from sources.base import BaseSource, TrendingItem
import enricher


def discover_sources() -> list[BaseSource]:
    """Auto-discover all BaseSource subclasses in the sources package."""
    for _finder, module_name, _ispkg in pkgutil.iter_modules(sources.__path__):
        if module_name == "base":
            continue
        importlib.import_module(f"sources.{module_name}")

    klasses = [
        cls
        for cls in BaseSource.__subclasses__()
        if cls.enabled
    ]
    return [cls() for cls in klasses]


def render_item(item: TrendingItem) -> str:
    parts = [f"- **[{item.title}]({item.url})**"]
    if item.language:
        parts[0] += f" `{item.language}`"
    if item.stars is not None:
        installs_label = item.extra.get("installs_label")
        if installs_label:
            parts[0] += f" — 📦 {installs_label}"
        else:
            parts[0] += f" — ⭐ {item.stars:,}"
    if item.description:
        parts.append(f"  *{item.description}*")
    annotation = item.extra.get("annotation")
    if annotation:
        parts.append(f"  > Why it's trending: {annotation}")
    reason = item.extra.get("relevance_reason")
    if reason:
        parts.append(f"  > Relevance: {reason}")
    return "\n".join(parts)


def render_report(
    now: datetime,
    items_by_source: dict[str, list[TrendingItem]],
    errors: dict[str, str],
    summary: str | None,
) -> str:
    today_str = now.strftime("%Y-%m-%d")
    generated_str = now.strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# whatsnew ☕ — {today_str}",
        f"*Generated on {generated_str}*",
        "",
    ]

    if summary:
        lines += ["## Summary", summary, ""]

    for source_name, items in items_by_source.items():
        lines.append(f"## {source_name}")
        if items:
            for item in items:
                lines.append(render_item(item))
        else:
            lines.append("*No items fetched.*")
        lines.append("")

    if errors:
        lines.append("## Errors")
        for source_name, error in errors.items():
            lines.append(f"- **{source_name}**: `{error}`")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    now = datetime.now(timezone.utc)
    today = now.date()
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    # Load .env for local development
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    discovered = discover_sources()
    print(f"Discovered {len(discovered)} source(s): {[s.name for s in discovered]}")

    items_by_source: dict[str, list[TrendingItem]] = {}
    errors: dict[str, str] = {}

    for source in discovered:
        print(f"Fetching: {source.name}...")
        try:
            items = source.fetch()
            items_by_source[source.name] = items
            print(f"  → {len(items)} item(s)")
        except Exception as exc:
            error_msg = str(exc)
            errors[source.name] = error_msg
            print(f"  → ERROR: {error_msg}")
            traceback.print_exc()

    if not items_by_source and errors:
        print("All sources failed. Aborting.")
        return 1

    # Enrich with Claude if API key is available
    print("Enriching with Claude AI...")
    try:
        items_by_source = enricher.filter_and_rank(items_by_source)
        items_by_source = enricher.annotate_items(items_by_source)
        summary = enricher.generate_summary(items_by_source)
    except Exception as exc:
        print(f"Enrichment failed (non-fatal): {exc}")
        summary = None

    report_md = render_report(now, items_by_source, errors, summary)

    dated_path = reports_dir / f"{today.isoformat()}.md"
    latest_path = reports_dir / "latest.md"

    dated_path.write_text(report_md, encoding="utf-8")
    latest_path.write_text(report_md, encoding="utf-8")
    print(f"Report written to {dated_path} and {latest_path}")

    # Weekly digest (Mondays only)
    try:
        digest = enricher.generate_weekly_digest(reports_dir, today)
        if digest:
            import calendar
            week_num = today.isocalendar()[1]
            year = today.isocalendar()[0]
            digest_path = reports_dir / f"weekly-{year}-W{week_num:02d}.md"
            header = f"# Weekly Tech Watch Digest — {year} W{week_num:02d}\n*Generated on {now.strftime('%Y-%m-%d %H:%M UTC')}*\n\n"
            digest_path.write_text(header + digest, encoding="utf-8")
            print(f"Weekly digest written to {digest_path}")
    except Exception as exc:
        print(f"Weekly digest failed (non-fatal): {exc}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
