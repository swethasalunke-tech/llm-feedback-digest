"""Feedback analysis using the Anthropic Claude API."""

from __future__ import annotations

import json
import re
from typing import Any

import anthropic


SYSTEM_PROMPT = """You are a product feedback analyst. For each feedback item you receive, classify it with:

- theme: one of [bug_report, feature_request, performance, ux_issue, billing, onboarding, praise, other]
- sentiment: one of [positive, neutral, negative]
- priority: one of [high, medium, low]
- summary: one concise sentence (max 20 words) capturing the core message

Return a JSON array where each element corresponds to the input item at the same index.
Each element must have exactly these keys: original_text, theme, sentiment, priority, summary.
Return only valid JSON with no markdown fences or commentary."""


class FeedbackAnalyzer:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def analyze_batch(self, feedback_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not feedback_items:
            return []

        numbered_items = []
        for idx, item in enumerate(feedback_items, start=1):
            parts = [f"{idx}. text: {item.get('text', '')}"]
            for field in ("source", "date", "user_id"):
                if item.get(field):
                    parts.append(f"   {field}: {item[field]}")
            numbered_items.append("\n".join(parts))

        user_content = "Analyze the following feedback items:\n\n" + "\n\n".join(numbered_items)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
        except anthropic.APIConnectionError as exc:
            raise RuntimeError(f"Connection to Anthropic API failed: {exc}") from exc
        except anthropic.RateLimitError as exc:
            raise RuntimeError("Anthropic API rate limit exceeded.") from exc
        except anthropic.APIStatusError as exc:
            raise RuntimeError(f"Anthropic API error {exc.status_code}: {exc.message}") from exc

        raw = message.content[0].text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            results: list[dict[str, Any]] = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Could not parse Claude response as JSON: {exc}") from exc

        if not isinstance(results, list) or len(results) != len(feedback_items):
            got = len(results) if isinstance(results, list) else type(results).__name__
            raise RuntimeError(
                f"Claude returned {got} result(s) for {len(feedback_items)} feedback "
                f"item(s); refusing to silently drop or misalign items."
            )

        for result, original in zip(results, feedback_items):
            result.setdefault("original_text", original.get("text", ""))

        return results