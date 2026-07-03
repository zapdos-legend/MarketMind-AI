"""Prompt construction helpers for MarketMind-AI."""

from __future__ import annotations

import campaign_engine


SUPPORTED_CONTENT_TYPES = {
    "Marketing Text",
    "Article",
    "Social Media Caption",
    "Poster",
    "Banner",
    "Pamphlet",
    "AI Marketing Pack",
}

VISUAL_DIRECTION_CONTENT_TYPES = {"Poster", "Banner", "Pamphlet"}


CONTENT_TYPE_INSTRUCTIONS = {
    "Marketing Text": (
        "Write persuasive marketing copy that is benefit-led, clear, and ready "
        "to use. Include a strong headline, concise body copy, and a clear CTA."
    ),
    "Article": (
        "Write a structured marketing article with a title, introduction, 3 to 5 "
        "useful sections, conclusion, and CTA. Keep the advice practical and "
        "audience-specific."
    ),
    "Social Media Caption": (
        "Write a platform-ready social media caption with four clear parts: hook, "
        "persuasive body, CTA, and relevant hashtags."
    ),
    "Poster": (
        "Create poster content only with: brand name, strong headline, supporting "
        "subheadline, exactly 3 benefits, CTA, and layout or visual direction. "
        "Do not generate or request an actual image."
    ),
    "Banner": (
        "Create banner content only with: short headline, one-line support text, "
        "CTA, and layout or visual direction. Do not generate or request an "
        "actual image."
    ),
    "Pamphlet": (
        "Create pamphlet content only with: headline, introduction, benefits, "
        "features, offer, CTA, contact section, and layout or visual direction."
    ),
    "AI Marketing Pack": (
        "Create a complete AI marketing pack 2.0 with: campaign strategy, "
        "marketing copy, poster copy, banner copy, pamphlet copy, social caption, "
        "CTA variations, and hashtag suggestions."
    ),
}


def _clean_value(value: object, default: str = "") -> str:
    """Return a safe, single-line string for prompt content."""
    if value is None:
        return default

    cleaned = " ".join(str(value).split())
    return cleaned if cleaned else default


def _normalize_content_type(value: object) -> str:
    """Return a supported content type, falling back to Marketing Text."""
    content_type = _clean_value(value, "Marketing Text")
    return content_type if content_type in SUPPORTED_CONTENT_TYPES else "Marketing Text"


def _format_optional_details(form_data: dict[str, object]) -> str:
    """Format only user-provided optional fields for the prompt."""
    optional_fields = (
        ("business_name", "Business name"),
        ("product_service", "Product/service"),
        ("audience", "Target audience"),
        ("platform", "Platform/channel"),
        ("tone", "Tone"),
        ("offer", "Offer/promotion"),
        ("notes", "Additional notes"),
    )
    details = []

    for field_name, label in optional_fields:
        value = _clean_value(form_data.get(field_name))
        if value:
            details.append(f"- {label}: {value}")

    if not details:
        return "No additional optional details were provided."

    return "\n".join(details)


def build_prompt(form_data: dict, strategy: dict | None = None) -> str:
    """Build a marketing content prompt from submitted form data and strategy."""
    if not isinstance(form_data, dict):
        form_data = {}

    content_type = _normalize_content_type(form_data.get("content_type"))
    topic = _clean_value(form_data.get("topic"), "the submitted marketing topic")
    optional_details = _format_optional_details(form_data)
    campaign_strategy = strategy or form_data.get("campaign_strategy") or campaign_engine.build_campaign_strategy(form_data)
    strategy_details = campaign_engine.format_strategy_for_prompt(campaign_strategy)
    primary_instruction = CONTENT_TYPE_INSTRUCTIONS[content_type]

    sections = [
        f"Create {content_type} for: {topic}.",
        "",
        "User-provided details:",
        optional_details,
        "",
        "Campaign strategy (use this as the source of truth before generating content):",
        strategy_details,
        "",
        "Primary task:",
        primary_instruction,
    ]

    if content_type in VISUAL_DIRECTION_CONTENT_TYPES:
        sections.extend(
            [
                "",
                "Important visual-output rule:",
                "Provide copy and layout/visual direction only. Do not create, "
                "embed, or describe the response as an actual generated image.",
            ]
        )

    if content_type == "AI Marketing Pack":
        sections.extend(
            [
                "",
                "Required pack sections:",
                "1. Campaign Strategy",
                "2. Marketing Copy",
                "3. Poster",
                "4. Banner",
                "5. Pamphlet",
                "6. Social Caption",
                "7. CTA Variations (exactly 5)",
                "8. Hashtag Suggestions (10-15)",
            ]
        )

    sections.extend(
        [
            "",
            "General guidance:",
            "- Generate from the campaign strategy first, not directly from the raw user prompt.",
            "- Use optional user details only to clarify or constrain the campaign strategy.",
            "- Keep the output practical, polished, and ready to adapt for a "
            "real marketing campaign.",
            "- Lead with benefits, audience relevance, emotional hooks, urgency "
            "when an offer is present, and action-oriented CTAs.",
            "- Never write prompt-transformer phrases such as 'Make X easier', "
            "'Make [prompt] easier', or generic AI filler.",
            "- Match the requested tone and platform when those details are "
            "provided.",
        ]
    )

    return "\n".join(sections)
