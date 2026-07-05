"""Visual component system for MarketMind-AI Phase 7.

Builds reusable, industry-aware creative component plans that sit after the
asset composition engine and before prompt/content rendering.
"""

from __future__ import annotations

from typing import Any

import industry_engine

COMPONENT_FIELDS = (
    "component_system_name", "primary_components", "secondary_components",
    "conversion_components", "trust_components", "decorative_components",
    "industry_specific_components", "component_hierarchy", "component_rules",
    "css_component_tokens", "html_component_plan", "asset_specific_components",
)

CORE_COMPONENTS = [
    "offer_badge", "cta_button", "benefit_card", "feature_chip", "trust_strip",
    "stat_card", "testimonial_card", "urgency_strip", "icon_bubble",
    "image_frame", "floating_label", "section_divider",
]

INDUSTRY_COMPONENTS = {
    "Fitness / App Launch": ["phone_mockup", "progress_streak_card", "workout_stat_card", "challenge_badge", "app_notification_card"],
    "Café / Food Offer": ["price_badge", "menu_chip", "breakfast_combo_card", "opening_hours_strip", "warm_review_card"],
    "EdTech / Workshop": ["course_card", "skill_progress_bar", "certificate_badge", "mentor_card", "enrollment_counter"],
    "Restaurant / Family Offer": ["reservation_card", "menu_offer_card", "family_table_badge", "chef_special_chip"],
    "Luxury / Real Estate": ["property_highlight_card", "amenity_grid", "site_visit_badge", "luxury_feature_strip", "location_pin_card"],
    "Healthcare / Clinic": ["doctor_card", "appointment_card", "credibility_badge", "service_card", "care_benefit_strip"],
    "Generic Professional": ["trust_strip", "stat_card", "testimonial_card", "offer_badge", "feature_chip"],
}

TOKENS = {
    "Fitness / App Launch": {"component_depth": "neon glass cards", "overlap": "high", "motion_cue": "streak lines", "surface": "dark app UI"},
    "Café / Food Offer": {"component_depth": "warm paper and ceramic cards", "overlap": "medium", "motion_cue": "steam curves", "surface": "cream café panels"},
    "EdTech / Workshop": {"component_depth": "clean dashboard cards", "overlap": "medium", "motion_cue": "progress bars", "surface": "professional blue panels"},
    "Restaurant / Family Offer": {"component_depth": "menu board cards", "overlap": "medium", "motion_cue": "ribbons and plate circles", "surface": "warm dining panels"},
    "Luxury / Real Estate": {"component_depth": "premium glass and gold rules", "overlap": "low", "motion_cue": "architectural linework", "surface": "dark editorial panels"},
    "Healthcare / Clinic": {"component_depth": "soft trust cards", "overlap": "low", "motion_cue": "calm rounded shapes", "surface": "white and aqua panels"},
    "Generic Professional": {"component_depth": "layered conversion cards", "overlap": "medium", "motion_cue": "accent orbs", "surface": "brand-gradient panels"},
}


def _text(*parts: object) -> str:
    return " ".join(str(p or "") for p in parts).lower()


def _family(form_data: dict[str, Any], composition_strategy: dict[str, Any], industry_alignment: dict[str, Any] | None = None) -> str:
    if industry_alignment:
        family_map = {"fitness_app": "Fitness / App Launch", "cafe_food": "Café / Food Offer", "edtech": "EdTech / Workshop", "restaurant": "Restaurant / Family Offer", "real_estate": "Luxury / Real Estate", "healthcare": "Healthcare / Clinic"}
        picked = family_map.get(str(industry_alignment.get("detected_industry")))
        if picked:
            return picked
    family = str(composition_strategy.get("layout_family") or "")
    if family in INDUSTRY_COMPONENTS:
        return family
    blob = _text(*form_data.values(), *composition_strategy.values())
    checks = [
        (("fitness", "workout", "app", "streak", "fitrush"), "Fitness / App Launch"),
        (("coffee", "cafe", "café", "breakfast", "sandwich", "brewnest"), "Café / Food Offer"),
        (("course", "workshop", "graduate", "career", "skillforge", "edtech"), "EdTech / Workshop"),
        (("restaurant", "reservation", "chef", "family dining"), "Restaurant / Family Offer"),
        (("apartment", "residence", "real estate", "site visit", "luxury"), "Luxury / Real Estate"),
        (("clinic", "doctor", "health", "appointment", "medical"), "Healthcare / Clinic"),
    ]
    for keywords, picked in checks:
        if any(k in blob for k in keywords):
            return picked
    return "Generic Professional"


def build_visual_component_strategy(
    form_data: dict[str, Any],
    campaign_strategy: dict[str, Any] | None = None,
    creative_strategy: dict[str, Any] | None = None,
    design_strategy: dict[str, Any] | None = None,
    composition_strategy: dict[str, Any] | None = None,
    industry_alignment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a structured component plan for richer rendered marketing assets."""
    campaign_strategy = campaign_strategy or {}
    creative_strategy = creative_strategy or {}
    design_strategy = design_strategy or {}
    composition_strategy = composition_strategy or {}
    content_type = str(form_data.get("content_type") or "Asset")
    alignment = industry_alignment or industry_engine.build_industry_alignment(form_data)
    family = _family(form_data, composition_strategy, alignment)
    industry = INDUSTRY_COMPONENTS[family]
    primary = industry[:3] + ["offer_badge", "cta_button"]
    secondary = industry[3:] + ["benefit_card", "feature_chip", "image_frame"]
    conversion = [c for c in ["offer_badge", "cta_button", "urgency_strip", "price_badge", "enrollment_counter", "reservation_card", "site_visit_badge", "appointment_card", "challenge_badge"] if c in primary + secondary + industry + CORE_COMPONENTS]
    trust = [c for c in ["trust_strip", "testimonial_card", "warm_review_card", "mentor_card", "credibility_badge", "doctor_card", "property_highlight_card"] if c in industry + CORE_COMPONENTS]
    decorative = ["icon_bubble", "floating_label", "section_divider"]
    asset_components = {
        "Poster": primary + ["floating_label", "stat_card"],
        "Banner": primary[:4] + secondary[:3] + ["trust_strip"],
        "Pamphlet": primary + secondary + trust + ["section_divider"],
    }.get(content_type, primary + secondary[:2])
    result = {
        "component_system_name": f"{family} Visual Component System",
        "primary_components": primary,
        "secondary_components": secondary,
        "conversion_components": conversion,
        "trust_components": trust or ["trust_strip"],
        "decorative_components": decorative,
        "industry_specific_components": industry,
        "component_hierarchy": [
            "Hero proof/product representation",
            "Offer and CTA conversion cluster",
            "Audience-relevant benefits",
            "Trust and urgency reinforcement",
            "Decorative depth and separation layers",
        ],
        "component_rules": [
            "Render components as visible blocks, not only as written directions.",
            "Use customer-facing copy only; never display internal component names or strategy labels in previews.",
            "Layer selected blocks with overlap, shadows, and foreground/background separation.",
            "Keep all HTML/CSS self-contained, responsive, and printable.",
        ],
        "css_component_tokens": TOKENS[family],
        "html_component_plan": [f"Use {name.replace('_', ' ')} to communicate customer value." for name in asset_components],
        "asset_specific_components": asset_components,
    }
    return industry_engine.validate_semantic_alignment(result, alignment)


def format_visual_components_for_prompt(strategy: dict[str, Any] | None) -> str:
    """Format the component plan for prompt context."""
    if not strategy:
        return "No visual component strategy was provided."
    lines: list[str] = []
    labels = {k: k.replace("_", " ").title() for k in COMPONENT_FIELDS}
    for key in COMPONENT_FIELDS:
        value = strategy.get(key, "")
        if isinstance(value, list):
            value = "; ".join(str(v) for v in value)
        elif isinstance(value, dict):
            value = "; ".join(f"{k}: {v}" for k, v in value.items())
        lines.append(f"- {labels[key]}: {value}")
    return "\n".join(lines)
