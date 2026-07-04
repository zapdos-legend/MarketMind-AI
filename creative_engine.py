"""Creative strategy helpers for MarketMind-AI.

This module turns the deterministic campaign strategy into a practical creative
brief: concept, hooks, visual direction, asset guidance, and CTA options. It is
kept separate from campaign_engine.py so the strategy layer remains stable while
creative execution can evolve independently.
"""

from __future__ import annotations

import re
from typing import Any

CREATIVE_FIELDS = (
    "campaign_concept",
    "creative_angle",
    "emotional_trigger",
    "primary_hook",
    "headline_options",
    "subheadline_options",
    "visual_direction",
    "color_mood",
    "imagery_direction",
    "offer_framing",
    "cta_options",
    "asset_guidance",
)


def _clean(value: Any, default: str = "") -> str:
    cleaned = " ".join(str(value or "").split())
    return cleaned or default


def _combined(form_data: dict[str, Any], strategy: dict[str, Any]) -> str:
    parts = [_clean(form_data.get(k)) for k in ("topic", "business_name", "product_service", "audience", "platform", "tone", "offer", "notes")]
    parts.extend(_clean(strategy.get(k)) for k in ("category", "target_audience", "offer_strategy", "key_marketing_message", "campaign_summary"))
    return " ".join(parts).lower()


def _category(text: str, strategy: dict[str, Any]) -> str:
    provided = _clean(strategy.get("category"))
    if provided:
        return provided
    if any(w in text for w in ("pizza", "restaurant", "food", "meal", "delivery")):
        return "food"
    if any(w in text for w in ("fitness", "workout", "gym", "health", "app")):
        return "fitness"
    if any(w in text for w in ("student", "college", "education", "course", "coaching")):
        return "education"
    if any(w in text for w in ("skin", "beauty", "glow")):
        return "beauty"
    return "general"


def _offer_hook(offer: str) -> str:
    pct = re.search(r"\b\d+%\s*off\b[^,.!]*", offer, re.I)
    if pct:
        return pct.group(0).strip().upper()
    if "trial" in offer.lower():
        return "FREE TRIAL STARTS NOW"
    if offer:
        return offer.upper()
    return "DON'T MISS THIS"


def build_creative_strategy(form_data: dict[str, Any], campaign_strategy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a structured creative strategy from form data and campaign strategy."""
    if not isinstance(form_data, dict):
        form_data = {}
    strategy = campaign_strategy or {}
    topic = _clean(form_data.get("topic"), _clean(strategy.get("source_prompt"), "Marketing campaign"))
    brand = _clean(form_data.get("business_name") or form_data.get("product_service"), "your brand")
    audience = _clean(strategy.get("target_audience") or form_data.get("audience"), "your best customers")
    offer = _clean(strategy.get("offer_strategy") or form_data.get("offer"), "Limited-time offer")
    cta = _clean(strategy.get("primary_cta"), "Get Started Today")
    value = _clean(strategy.get("value_proposition"), f"A timely offer for {audience}")
    text = _combined(form_data, strategy)
    cat = _category(text, strategy)

    if cat == "food":
        concept = "Weekend Pizza Rush" if "weekend" in text or "pizza" in text else "Fresh Flavor Fast"
        angle = "Skip cooking and make the weekend feel easy, hot, and shareable."
        trigger = "Convenience, appetite, and urgency"
        primary_hook = _offer_hook(offer) if "off" in offer.lower() else "FRESH PIZZA. FAST WEEKEND WINS."
        headlines = [primary_hook, "Skip Cooking Tonight.", "Fresh Pizza. Half The Price."]
        subheads = ["Hot pies, happy tables, and a weekend deal made for families and students.", value, "Bring everyone together without paying full price."]
        visual = "Warm pizza imagery, family and friends sharing food, bold offer badge, appetizing red/orange contrast, and a simple order-first layout."
        color = "Warm reds, oven orange, golden cheese yellow, and deep crust browns"
        imagery = "Close-up melted cheese, fresh slices being shared, delivery-ready boxes, and a prominent weekend offer badge."
        ctas = [cta, "Claim This Weekend Deal", "Get Pizza Tonight", "Feed Your Crew", "Tap To Order"]
    elif cat == "fitness":
        concept = "FitRush Campus Kickstart"
        angle = "Make fitness feel quick, social, and doable between classes."
        trigger = "Momentum, confidence, and low-friction commitment"
        primary_hook = "START STRONG THIS WEEK" if "trial" not in offer.lower() else "FREE 7-DAY FITNESS KICKSTART"
        headlines = [primary_hook, "Train Between Classes.", "Your Campus Fitness Streak Starts Here."]
        subheads = ["Quick workouts and progress tracking built for busy college schedules.", value, "Try the routine before you commit."]
        visual = "Energetic mobile app visuals, campus lifestyle moments, motion lines, progress cards, and a bold trial CTA."
        color = "Deep navy, electric green, bright orange, and clean white"
        imagery = "Students using a fitness app, quick workout snapshots, streak/progress UI cards, and campus energy."
        ctas = [cta, "Start Your Free Trial", "Try FitRush Today", "Build Your Streak", "Get Moving Now"]
    else:
        concept = f"{brand} Action Campaign"
        angle = f"Show {audience} the clearest reason to care now."
        trigger = "Clarity, relevance, and urgency"
        primary_hook = _offer_hook(offer) if offer else _clean(strategy.get("key_marketing_message"), topic).upper()
        headlines = [primary_hook, f"{brand} Makes It Easier.", "A Better Reason To Start Today."]
        subheads = [value, f"Built for {audience} with a clear next step.", "Simple value, strong proof, and a timely offer."]
        visual = "Clean high-contrast layout, bold headline hierarchy, benefit cards, offer badge, and action-focused CTA area."
        color = "Confident blues, bright accent colors, and clean neutral space"
        imagery = "Audience-relevant lifestyle image, product/service cue, proof points, and a clear CTA button."
        ctas = [cta, "Claim Your Offer", "Start Today", "See How It Works", "Get Started"]

    offer_framing = offer if offer else primary_hook
    return {
        "campaign_concept": concept,
        "creative_angle": angle,
        "emotional_trigger": trigger,
        "primary_hook": primary_hook,
        "headline_options": list(dict.fromkeys(headlines))[:3],
        "subheadline_options": list(dict.fromkeys(subheads))[:3],
        "visual_direction": visual,
        "color_mood": color,
        "imagery_direction": imagery,
        "offer_framing": offer_framing,
        "cta_options": list(dict.fromkeys(ctas))[:5],
        "asset_guidance": {
            "poster": f"Lead with '{primary_hook}', use the strongest subheadline, place '{offer}' as a badge, and end with {ctas[0]}.",
            "banner": "Use the shortest punchiest headline, make the offer dominant, and keep the CTA urgent.",
            "pamphlet": f"Use '{concept}' as the title, open with the creative angle, then explain benefits, offer, and CTA options.",
            "social_caption": "Open with the primary hook, keep the body conversational, and close with a direct CTA plus relevant hashtags.",
        },
    }


def format_creative_for_prompt(creative: dict[str, Any] | None) -> str:
    """Format creative strategy as prompt context for downstream generation."""
    if not creative:
        return "No creative strategy was provided."
    labels = {
        "campaign_concept": "Campaign Concept",
        "creative_angle": "Creative Angle",
        "emotional_trigger": "Emotional Trigger",
        "primary_hook": "Primary Hook",
        "headline_options": "Headline Options",
        "subheadline_options": "Subheadline Options",
        "visual_direction": "Visual Direction",
        "color_mood": "Color Mood",
        "imagery_direction": "Imagery Direction",
        "offer_framing": "Offer Framing",
        "cta_options": "CTA Options",
        "asset_guidance": "Asset Guidance",
    }
    lines: list[str] = []
    for key in CREATIVE_FIELDS:
        value = creative.get(key, "")
        if isinstance(value, list):
            value = "; ".join(str(item) for item in value)
        elif isinstance(value, dict):
            value = "; ".join(f"{k}: {v}" for k, v in value.items())
        lines.append(f"- {labels[key]}: {value}")
    return "\n".join(lines)
