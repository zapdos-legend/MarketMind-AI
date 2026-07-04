"""Design intelligence helpers for MarketMind-AI.

This module adds a deterministic visual design layer between creative strategy
and prompt/content generation. Campaign strategy decides what to say, creative
strategy decides how to say it, and design strategy decides how the final asset
should look and be composed.
"""

from __future__ import annotations

from typing import Any

DESIGN_FIELDS = (
    "design_concept",
    "layout_type",
    "visual_hierarchy",
    "typography_style",
    "color_palette",
    "background_style",
    "image_direction",
    "composition_rules",
    "component_plan",
    "asset_layouts",
    "design_notes",
)


def _clean(value: Any, default: str = "") -> str:
    cleaned = " ".join(str(value or "").split())
    return cleaned or default


def _combined(form_data: dict[str, Any], campaign_strategy: dict[str, Any], creative_strategy: dict[str, Any]) -> str:
    parts = [_clean(form_data.get(k)) for k in ("topic", "business_name", "product_service", "audience", "platform", "tone", "offer", "notes")]
    parts.extend(_clean(campaign_strategy.get(k)) for k in ("category", "target_audience", "offer_strategy", "value_proposition", "key_marketing_message", "campaign_summary"))
    parts.extend(_clean(creative_strategy.get(k)) for k in ("campaign_concept", "visual_direction", "color_mood", "imagery_direction", "offer_framing"))
    return " ".join(parts).lower()


def _category(text: str, campaign_strategy: dict[str, Any]) -> str:
    provided = _clean(campaign_strategy.get("category"))
    if provided == "food" and any(word in text for word in ("cafe", "café", "coffee", "breakfast", "sandwich")):
        return "cafe_breakfast"
    if provided == "food" and any(word in text for word in ("pizza", "pizzeria")):
        return "food_pizza"
    if provided in {"fitness", "education", "beauty"}:
        return provided
    if any(word in text for word in ("fitness", "gym", "workout", "training")) and "app" in text:
        return "fitness"
    if any(word in text for word in ("pizza", "pizzeria")):
        return "food_pizza"
    if any(word in text for word in ("cafe", "café", "coffee", "breakfast", "sandwich")):
        return "cafe_breakfast"
    if any(word in text for word in ("salon", "beauty", "skin", "skincare", "glow", "hair")):
        return "beauty"
    if any(word in text for word in ("education", "course", "class", "coaching", "iit", "jee", "student")):
        return "education"
    return "generic"


def build_design_strategy(
    form_data: dict[str, Any],
    campaign_strategy: dict[str, Any] | None = None,
    creative_strategy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a structured visual design strategy for generated assets."""
    if not isinstance(form_data, dict):
        form_data = {}
    campaign_strategy = campaign_strategy or {}
    creative_strategy = creative_strategy or {}
    text = _combined(form_data, campaign_strategy, creative_strategy)
    cat = _category(text, campaign_strategy)
    offer = _clean(campaign_strategy.get("offer_strategy") or creative_strategy.get("offer_framing") or form_data.get("offer"), "Limited-time offer")

    library: dict[str, dict[str, Any]] = {
        "fitness": {
            "design_concept": "High-energy student fitness launch",
            "layout_type": "Bold athletic app launch poster",
            "visual_hierarchy": ["Big headline", "Student fitness/app visual", "Free trial badge", "App benefit cards", "CTA"],
            "typography_style": "Oversized condensed bold headline with compact uppercase labels",
            "color_palette": ["black", "neon green", "white", "electric orange"],
            "background_style": "Dark gym or student lifestyle visual with neon motion accents",
            "image_direction": "Use students training, mobile fitness UI cards, progress streaks, and gym/campus energy.",
            "composition_rules": ["Keep headline oversized on the left", "Place image/product energy on the right", "Use neon accents only for key actions", "Keep strategy wording out of asset copy"],
            "component_plan": ["Logo top-left", "Offer badge top-right", "Large headline left", "Student/gym image right", "Benefits row below headline", "CTA bottom-left", "Footer trust strip"],
        },
        "food_pizza": {
            "design_concept": "Hot weekend pizza deal",
            "layout_type": "Appetite-first offer poster with food hero focus",
            "visual_hierarchy": ["Large offer badge", "Pizza hero image", "Weekend headline", "Family/student benefits", "Order CTA"],
            "typography_style": "Chunky bold headline with rounded friendly offer type",
            "color_palette": ["tomato red", "oven orange", "cheese yellow", "warm cream"],
            "background_style": "Warm pizzeria/table texture with melted cheese close-up energy",
            "image_direction": "Use fresh pizza slices, sharing moments, delivery boxes, and family/friend cues.",
            "composition_rules": ["Make food image the visual anchor", "Keep offer badge large and high contrast", "Use warm gradients", "CTA must be immediately visible"],
            "component_plan": ["Brand/logo top", "Large deal badge", "Pizza image hero", "Benefits for families and students", "Order CTA", "Weekend urgency strip"],
        },
        "cafe_breakfast": {
            "design_concept": "Warm morning productivity combo",
            "layout_type": "Breakfast hero banner",
            "visual_hierarchy": ["Offer price", "Coffee and sandwich visual", "Morning headline", "CTA", "Time window"],
            "typography_style": "Warm display headline plus clean bold offer price",
            "color_palette": ["coffee brown", "cream", "gold", "soft white"],
            "background_style": "Warm café table, coffee steam, morning light, and breakfast texture",
            "image_direction": "Use coffee plus sandwich/breakfast visuals; avoid pizza imagery for café assets.",
            "composition_rules": ["Lead with the offer when price is present", "Use warm daylight contrast", "Keep CTA large", "Reserve a small time-window area"],
            "component_plan": ["Brand mark", "Prominent combo price", "Coffee + sandwich hero", "Morning benefit line", "CTA button", "Time-window tag"],
        },
        "beauty": {
            "design_concept": "Soft premium transformation story",
            "layout_type": "Elegant beauty service/package layout",
            "visual_hierarchy": ["Transformation promise", "Service/package cards", "Trust cues", "Offer", "CTA"],
            "typography_style": "Elegant high-contrast headline with clean premium body text",
            "color_palette": ["blush pink", "soft mauve", "cream", "deep plum"],
            "background_style": "Soft gradient, skin/glow texture, premium whitespace",
            "image_direction": "Use transformation cues, salon/beauty closeups, clean product/service details, and soft lighting.",
            "composition_rules": ["Use generous whitespace", "Cards should feel premium", "Avoid clutter", "Use trust cues near CTA"],
            "component_plan": ["Logo", "Elegant headline", "Hero transformation visual", "Service package cards", "Trust strip", "CTA"],
        },
        "education": {
            "design_concept": "Clean learning credibility campaign",
            "layout_type": "Course-card education layout",
            "visual_hierarchy": ["Outcome headline", "Credibility badges", "Course cards", "Proof", "Enrollment CTA"],
            "typography_style": "Clean bold academic headline with readable structured sections",
            "color_palette": ["deep blue", "purple", "white", "light lavender"],
            "background_style": "Clean learning environment with subtle academic shapes",
            "image_direction": "Use students learning, course cards, faculty/proof badges, and clear progress cues.",
            "composition_rules": ["Make proof visible", "Keep sections scannable", "Use cards for courses/features", "CTA should feel enrollment-ready"],
            "component_plan": ["Logo", "Outcome headline", "Credibility badges", "Course/benefit cards", "Demo/offer block", "CTA"],
        },
        "generic": {
            "design_concept": "Clean modern commercial campaign",
            "layout_type": "Modern conversion-focused marketing layout",
            "visual_hierarchy": ["Strong headline", "Offer badge", "Benefits", "Relevant visual", "CTA"],
            "typography_style": "Bold modern headline with simple readable supporting text",
            "color_palette": ["indigo", "cyan", "white", "slate"],
            "background_style": "Clean gradient with audience-relevant lifestyle/product visual",
            "image_direction": "Use a polished lifestyle or product image that matches the audience and offer.",
            "composition_rules": ["Lead with one main message", "Use offer badge only for real offers", "Keep benefits in cards", "CTA must be high contrast"],
            "component_plan": ["Logo", "Headline", "Offer badge", "Benefit cards", "Visual block", "CTA", "Proof strip"],
        },
    }
    design = dict(library[cat])
    design["asset_layouts"] = {
        "poster": ["Logo top-left", "Offer badge top-right", "Large headline zone", "Audience-relevant hero visual", "Three benefit cards", "CTA block", "Footer trust/contact strip"],
        "banner": ["Offer-first hero area when offer is strong", "Short headline", "Support line", "Large CTA", "Hero visual cropped to one side", "Minimal proof/time-window chip"],
        "pamphlet": ["Cover panel", "Audience/problem panel", "Benefits panel", "Features/service panel", "Offer/CTA panel", "Contact/trust panel"],
    }
    design["design_notes"] = [
        f"Use '{offer}' as a customer-facing offer cue when relevant.",
        "Final assets must show polished marketing copy only, not internal strategy labels.",
        "Prefer accessible contrast and scannable spacing for print and web previews.",
    ]
    design["category"] = cat
    return design


def format_design_for_prompt(design_strategy: dict[str, Any] | None) -> str:
    """Format design strategy as prompt context for downstream generation."""
    if not design_strategy:
        return "No design strategy was provided."
    labels = {
        "design_concept": "Design Concept",
        "layout_type": "Layout Type",
        "visual_hierarchy": "Visual Hierarchy",
        "typography_style": "Typography Style",
        "color_palette": "Color Palette",
        "background_style": "Background Style",
        "image_direction": "Image Direction",
        "composition_rules": "Composition Rules",
        "component_plan": "Component Plan",
        "asset_layouts": "Asset Layouts",
        "design_notes": "Design Notes",
    }
    lines: list[str] = []
    for key in DESIGN_FIELDS:
        value = design_strategy.get(key, "")
        if isinstance(value, list):
            value = "; ".join(str(item) for item in value)
        elif isinstance(value, dict):
            value = "; ".join(f"{name}: {', '.join(items) if isinstance(items, list) else items}" for name, items in value.items())
        lines.append(f"- {labels[key]}: {value}")
    return "\n".join(lines)
