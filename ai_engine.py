"""AI analysis helpers for MarketMind-AI.

The app calls ``analyze(prompt)`` with a ready-made marketing prompt. When an
OpenAI API key is configured, this module can request an AI-generated strategy.
Without a key, it returns a deterministic local strategy so the app remains
useful in development and demos.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


OPENAI_API_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-4.1-mini"
REQUEST_TIMEOUT_SECONDS = 30


def _shorten(text: str, limit: int = 260) -> str:
    """Return a compact preview of text for the fallback response."""
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3].rstrip()}..."


def _local_fallback(prompt: str, reason: str | None = None) -> str:
    """Build a deterministic, practical marketing strategy without an API call."""
    prompt_preview = _shorten(prompt) or "the submitted business topic"
    note = f"\n\nNote: Using local fallback because {reason}." if reason else ""

    return f"""Marketing Strategy

Summary of the opportunity
The request focuses on: {prompt_preview}
This is an opportunity to turn a clear customer problem into a simple campaign
that explains who the offer helps, why it is different, and what action the
audience should take next.

Positioning and key message
Position the offer as a practical, low-friction solution for the target audience.
Use a message like: "Get the outcome you want faster, with less guesswork and a
clear next step." Keep the language specific, benefit-led, and easy to repeat.

Channels to prioritize
1. Search-friendly content: Publish helpful pages, guides, or posts that answer
   common buyer questions and build trust over time.
2. Social proof channels: Share testimonials, short case studies, demos, and
   before-and-after examples where the audience already spends time.
3. Email follow-up: Capture interested visitors and send a short nurture sequence
   with education, proof, and a clear call to action.

Actionable campaign ideas
1. Create a beginner-friendly landing page with one primary call to action.
2. Publish three educational posts that address the audience's biggest concerns.
3. Launch a small test campaign around one offer, one audience, and one channel.
4. Collect customer questions and turn the best answers into social content.
5. Add a simple lead magnet, checklist, or consultation offer to capture demand.

Success metrics to track
- Conversion rate from landing page visits to leads or purchases.
- Cost per lead or cost per acquisition for paid tests.
- Email sign-up rate and email reply/click rate.
- Engagement on educational content and social proof posts.
- Number of qualified conversations created each week.

Risks, assumptions, and next steps
The main risk is trying too many channels before the core message is proven.
Start with one audience segment, test one clear promise, measure results weekly,
and improve the offer based on real customer feedback.{note}"""


def _call_openai(prompt: str, api_key: str) -> str:
    """Call OpenAI's Responses API and return the generated text."""
    payload = {
        "model": os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
        "input": prompt,
        "instructions": (
            "You are a helpful marketing strategist. Return a clear, practical, "
            "beginner-friendly marketing plan with headings and actionable steps."
        ),
    }

    request = urllib.request.Request(
        OPENAI_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        data = json.loads(response.read().decode("utf-8"))

    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    for item in data.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()

    raise ValueError("OpenAI response did not include usable text")


def analyze(prompt: str) -> str:
    """Analyze a marketing prompt using OpenAI when available, otherwise locally."""
    if not isinstance(prompt, str):
        return _local_fallback(str(prompt), "the prompt was not provided as text")

    clean_prompt = prompt.strip()
    if not clean_prompt:
        return _local_fallback("", "the prompt was empty")

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return _local_fallback(clean_prompt)

    try:
        return _call_openai(clean_prompt, api_key)
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return _local_fallback(clean_prompt, f"the OpenAI request could not be completed ({exc})")
