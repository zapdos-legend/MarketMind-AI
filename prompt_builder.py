"""Prompt construction helpers for MarketMind-AI."""

from __future__ import annotations


def _clean_value(value: object, default: str = "Not specified") -> str:
    """Return a safe, single-line string for prompt content."""
    if value is None:
        return default

    cleaned = " ".join(str(value).split())
    return cleaned if cleaned else default


def build_prompt(form_data: dict) -> str:
    """Build a clear marketing strategy prompt from submitted form data."""
    if not isinstance(form_data, dict):
        form_data = {}

    topic = _clean_value(form_data.get("topic"), "the submitted business topic")
    audience = _clean_value(form_data.get("audience"))
    goal = _clean_value(form_data.get("goal"))
    budget = _clean_value(form_data.get("budget"))
    timeline = _clean_value(form_data.get("timeline"))
    competitors = _clean_value(form_data.get("competitors"))
    channels = _clean_value(form_data.get("channels"))
    notes = _clean_value(form_data.get("notes"))

    return f"""Create a practical marketing strategy for: {topic}.

Use these details from the user:
- Target audience: {audience}
- Main goal: {goal}
- Budget: {budget}
- Timeline: {timeline}
- Competitors or alternatives: {competitors}
- Preferred channels: {channels}
- Additional notes: {notes}

Please include:
1. A short summary of the opportunity.
2. Recommended positioning and key message.
3. The best marketing channels to prioritize.
4. 3 to 5 actionable campaign ideas.
5. Simple success metrics to track.
6. Any important risks, assumptions, or next steps.

Keep the response clear, realistic, and useful for a beginner-friendly marketing plan."""
