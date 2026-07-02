"""AI content generation helpers for MarketMind-AI.

The app calls ``analyze(prompt)`` with a ready-made marketing content prompt.
When an OpenAI API key is configured, this module asks OpenAI to follow that
prompt directly. Without a key, it returns deterministic local content so the
app remains useful in development and demos.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request


OPENAI_API_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-4.1-mini"
REQUEST_TIMEOUT_SECONDS = 30
VISUAL_CONTENT_TYPES = {"Poster", "Banner", "Pamphlet"}
SUPPORTED_CONTENT_TYPES = (
    "Marketing Text",
    "Article",
    "Social Media Caption",
    "Poster",
    "Banner",
    "Pamphlet",
    "AI Marketing Pack",
)


def _shorten(text: str, limit: int = 260) -> str:
    """Return a compact preview of text for the fallback response."""
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3].rstrip()}..."


def _extract_content_type(prompt: str) -> str:
    """Infer the requested content type from a prompt_builder.py prompt."""
    first_line = prompt.splitlines()[0] if prompt.splitlines() else ""
    match = re.match(r"Create (.+?) for:", first_line)
    if match and match.group(1) in SUPPORTED_CONTENT_TYPES:
        return match.group(1)
    return "Marketing Text"


def _extract_topic(prompt: str) -> str:
    """Infer the topic from the first line of a prompt_builder.py prompt."""
    first_line = prompt.splitlines()[0] if prompt.splitlines() else ""
    match = re.match(r"Create .+? for: (.+?)\.\s*$", first_line)
    if match:
        return match.group(1).strip()
    return _shorten(prompt) or "the submitted marketing topic"


def _extract_detail(prompt: str, label: str) -> str:
    """Return a user-provided detail from the prompt, if present."""
    prefix = f"- {label}:"
    for line in prompt.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    return ""


def _fallback_context(prompt: str) -> dict[str, str]:
    """Build reusable context values for local content generation."""
    topic = _extract_topic(prompt)
    business_name = _extract_detail(prompt, "Business name")
    product_service = _extract_detail(prompt, "Product/service")
    audience = _extract_detail(prompt, "Target audience")
    platform = _extract_detail(prompt, "Platform/channel")
    tone = _extract_detail(prompt, "Tone")
    offer = _extract_detail(prompt, "Offer/promotion")

    brand = business_name or product_service or topic
    audience_text = f" for {audience}" if audience else ""
    offer_text = f" {offer}" if offer else ""
    platform_text = f" on {platform}" if platform else ""
    tone_text = f" Use a {tone} tone." if tone else ""

    return {
        "topic": topic,
        "brand": brand,
        "audience_text": audience_text,
        "offer_text": offer_text,
        "platform_text": platform_text,
        "tone_text": tone_text,
    }


def _visual_guidance(content_type: str) -> str:
    """Return visual/layout guidance for copy-only visual formats."""
    if content_type == "Poster":
        return "Place the headline at the top, one supporting benefit in the center, and the CTA in a bold bottom block. Use one hero visual area and high-contrast colors."
    if content_type == "Banner":
        return "Use a left-aligned headline, a short benefit line, and a right-aligned CTA button. Keep generous whitespace for quick scanning."
    return "Organize copy into front, inside, and back panels with clear section breaks, concise bullets, and a repeated CTA on the back panel."


def _local_fallback(prompt: str, reason: str | None = None) -> str:
    """Build deterministic marketing content without overriding the prompt."""
    content_type = _extract_content_type(prompt)
    context = _fallback_context(prompt)
    brand = context["brand"]
    topic = context["topic"]
    audience_text = context["audience_text"]
    offer_text = context["offer_text"]
    platform_text = context["platform_text"]
    tone_text = context["tone_text"]
    note = f"\n\nNote: Using local fallback because {reason}." if reason else ""

    if content_type == "Article":
        return f"""# {topic}: A Smarter Way to Get Results

## Introduction
{brand} helps make {topic} easier to understand, choose, and act on{audience_text}.{tone_text}

## Why it matters
Customers want clear benefits, proof, and a simple next step. Focus the message on the outcome they care about most and remove friction from the decision.

## What to do next
Use concise copy, helpful examples, and a direct CTA so readers know exactly how to move forward.

## CTA
Explore {brand} today{offer_text} and take the next step with confidence.{note}"""

    if content_type == "Social Media Caption":
        return f"""Hook: Ready to make {topic} simpler?

{brand} gives you a clearer way to move from interest to action{audience_text}{platform_text}. Focus on the outcome, skip the guesswork, and take the next step today.{tone_text}

CTA: Learn more and get started{offer_text}.

Hashtags: #Marketing #BrandGrowth #SmallBusiness #ContentMarketing #GetStarted{note}"""

    if content_type in VISUAL_CONTENT_TYPES:
        if content_type == "Pamphlet":
            body = f"""Front panel: {brand}\nHeadline: Make {topic} easier\nSubcopy: Clear benefits, practical details, and a simple next step{audience_text}.\n\nInside panel 1: Why choose this\n- Benefit-led message focused on the customer's goal\n- Simple explanation of what is offered\n- Proof points or details that build trust\n\nInside panel 2: Offer\nHighlight:{offer_text or ' a clear reason to act now'}\n\nBack panel CTA: Contact {brand} to learn more and get started."""
        else:
            body = f"""Headline: Make {topic} easier\nSupporting copy: {brand} helps you get clear, practical results{audience_text}.\nCTA: Get started{offer_text}."""

        return f"""{content_type} Copy
{body}

Layout / Visual Direction
{_visual_guidance(content_type)} Do not generate an actual image.{note}"""

    if content_type == "AI Marketing Pack":
        return f"""Brief Strategy
Position {brand} as a clear, practical solution for {topic}{audience_text}. Lead with the most immediate benefit, support it with proof, and drive every asset toward one CTA.

Social Caption
Ready to make {topic} easier? {brand} helps you move forward with clarity and confidence{platform_text}. Learn more today{offer_text}.

Poster Copy
Headline: Make {topic} easier
Supporting copy: Clear benefits. Simple next step. Built for real results.
CTA: Get started today.

Banner Copy
Headline: Better {topic} starts here
Copy: Discover a simpler way forward.
CTA: Learn more

Hashtags
#Marketing #BrandGrowth #ContentMarketing #SmallBusiness #CampaignReady

CTA
Choose {brand} and take the next step today{offer_text}.{note}"""

    return f"""Headline
Make {topic} easier with {brand}

Body Copy
Turn interest into action with clear, benefit-led messaging{audience_text}. {brand} helps people understand the value quickly, see why it matters, and know exactly what to do next.{tone_text}

CTA
Get started today{offer_text}.{note}"""


def _call_openai(prompt: str, api_key: str) -> str:
    """Call OpenAI's Responses API and return the generated text."""
    payload = {
        "model": os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
        "input": prompt,
        "instructions": (
            "You are a helpful AI marketing content generator. Follow the user's "
            "prompt exactly, including requested content type, sections, tone, "
            "platform, and visual-output rules. Do not replace the request with "
            "a generic marketing strategy template. For poster, banner, and "
            "pamphlet requests, provide copy plus layout or visual guidance only."
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
    """Generate marketing content using OpenAI when available, otherwise locally."""
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
