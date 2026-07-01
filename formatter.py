"""Generates a markdown digest from analyzed feedback items."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

import httpx


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
THEME_LABELS: dict[str, str] = {
    "bug_report": "Bug Reports",
    "feature_request": "Feature Requests",
    "performance": "Performance",
    "ux_issue": "UX Issues",
    "billing": "Billing",
    "onboarding": "Onboarding",
    "praise": "Praise",
    "other": "Other",
}


def generate_digest(analyzed_items: list[dict]) -> str:
    if not analyzed_items:
        return "# Weekly Feedback Digest\n\nNo feedback items to display.\n"
    total = len(analyzed_items)
    sentiment_counts = defaultdict(int)
    theme_groups = defaultdict(list)
    for item in analyzed_items:
        sentiment_counts[item.get("sentiment", "neutral")] += 1
        theme_groups[item.get("theme", "other")].append(item)
    for theme in theme_groups:
        theme_groups[theme].sort(key=lambda x: PRIORITY_ORDERed
get(x.get("priority", "low"), 2))
    today = date.today().isoformat()
    lines = ["# Weekly Feedback Digest", "", f"Generated: {today}", "", "## Summary", "", f"Total items: {total}", "", "Sentiment breakdown:", ""]
    for s in ("positive", "neutral", "negative"):
        c = sentiment_counts.get(s, 0)
        lines.append(f"- {s.capitalize()}: {c} ({round(c/total*100)}%)")
    lines += ["", "---", ""]
    for tkey in sorted(theme_groups):
        label = THEME_LABELS.get(tkey, tkey.replace("_", " ").title())
        lines.append(f"## {label}"); lines.append("")
        for item in theme_groups[tkey]:
            lines += [f"**[{item.get('priority','low').upper()}]** {item.get('summary','').strip()}", "", f"> {item.get('original_text','').strip()}", "", f"_Sentiment: {item.get('sentiment','neutral')}_", ""]
    return "\n".join(lines)


def render_slack_blocks(items):
    if not items: return [{"type":"section","text":{"type":"mrkdwn","text":"No items."}}]
    total = len(items)
    scnt = defaultdict(int)
    for i in items: scnt[i.get("sentiment","neutral")] += 1
    blocks = [{"type":"header","text":{"type":"plain_text","text":"Weekly Feedback Digest","emoji":True}},{"type":"context","elements":[{"type":"mrkdwn","text":f"Generated: {date.today().isoformat()}"}]},{"type":"section","text":{"type":"mrkdwn","text":f"*Total:* {total} | :yellow_circle: {scnt.get('neutral',0)} :: red_circle: {scnt.get('negative',0)}"}},{"type":"divider"}]
    return blocks


def send_to_slack(webhook_url, items):
    import httpx
    r = httpx.post(webhook_url, json={"blocks":render_slack_blocks(items)},timeout=10)
    r.raise_for_status()
