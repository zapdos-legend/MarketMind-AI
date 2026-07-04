"""Asset composition strategy engine for MarketMind-AI.

Converts campaign, creative, and design strategy into concrete layout direction
for poster, banner, and pamphlet HTML previews.
"""

from __future__ import annotations

from typing import Any

COMPOSITION_FIELDS = (
    "composition_name", "layout_family", "visual_structure", "hero_zone",
    "headline_zone", "offer_zone", "cta_zone", "trust_zone", "benefit_zone",
    "image_zone", "background_layers", "decorative_elements", "spacing_rules",
    "responsive_rules", "css_tokens", "html_sections", "asset_specific_notes",
)


def _text(*parts: object) -> str:
    return " ".join(str(p or "") for p in parts).lower()


def _pick_family(form_data: dict[str, Any], campaign_strategy: dict[str, Any], creative_strategy: dict[str, Any], design_strategy: dict[str, Any]) -> str:
    blob = _text(
        form_data.get("content_type"), form_data.get("topic"), form_data.get("business_name"),
        form_data.get("product_service"), form_data.get("audience"), form_data.get("platform"),
        form_data.get("tone"), form_data.get("offer"), form_data.get("notes"),
        *campaign_strategy.values(), *creative_strategy.values(), *design_strategy.values(),
    )
    checks = [
        (("fitness", "gym", "workout", "athlete", "training", "exercise", "fitrush"), "Fitness / App Launch"),
        (("coffee", "café", "cafe", "breakfast", "sandwich", "brew", "morning"), "Café / Food Offer"),
        (("course", "workshop", "ai career", "training", "edtech", "learning", "graduate", "skillforge"), "EdTech / Workshop"),
        (("restaurant", "dinner", "family dining", "menu", "reservation", "meal"), "Restaurant / Family Offer"),
        (("apartment", "property", "real estate", "residence", "residences", "architecture", "site visit", "luxury"), "Luxury / Real Estate"),
        (("clinic", "healthcare", "doctor", "hospital", "appointment", "medical", "dental"), "Healthcare / Clinic"),
    ]
    for keywords, family in checks:
        if any(k in blob for k in keywords):
            return family
    return "Generic Professional"


def build_asset_composition(form_data: dict[str, Any], campaign_strategy: dict[str, Any] | None = None, creative_strategy: dict[str, Any] | None = None, design_strategy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a structured composition dictionary for the requested asset."""
    campaign_strategy = campaign_strategy or {}
    creative_strategy = creative_strategy or {}
    design_strategy = design_strategy or {}
    content_type = str(form_data.get("content_type") or "Asset")
    family = _pick_family(form_data, campaign_strategy, creative_strategy, design_strategy)
    specs: dict[str, dict[str, Any]] = {
        "Fitness / App Launch": dict(name="Athletic App Launch Split", structure="Bold split layout with oversized kinetic type, workout visual, floating app benefit cards, neon offer badge, and high-energy CTA.", hero="Right-side athlete/app hero with diagonal crop and glow.", bg=["charcoal gradient", "electric green/cyan glows", "diagonal speed lines"], decor=["neon rings", "floating app cards", "energy ticks"], tokens={"primary":"#08111f","accent":"#39ff88","secondary":"#22d3ee","radius":"28px"}),
        "Café / Food Offer": dict(name="Warm Morning Combo", structure="Horizontal cozy breakfast layout with large food image, prominent price badge, warm CTA, and soft café textures.", hero="Large coffee/breakfast image zone with steam-like accents.", bg=["espresso-to-cream gradient", "soft morning light", "rounded cozy blobs"], decor=["steam curves", "price badge", "bean dots"], tokens={"primary":"#4a2c1a","accent":"#f59e0b","secondary":"#fef3c7","radius":"34px"}),
        "EdTech / Workshop": dict(name="Professional Learning Conversion", structure="Clean learning layout with course card, skill/progress elements, mentor/trust area, and registration CTA.", hero="Course/workshop card with progress bars and learning chips.", bg=["white/blue workspace", "subtle grid", "LinkedIn-friendly accents"], decor=["progress bars", "skill pills", "mentor badge"], tokens={"primary":"#172554","accent":"#2563eb","secondary":"#a855f7","radius":"22px"}),
        "Restaurant / Family Offer": dict(name="Family Dining Offer Table", structure="Warm dining layout with menu cards, food imagery emphasis, family proof, and reservation CTA.", hero="Food platter or table scene with menu offer cards.", bg=["tomato red gradient", "warm table texture", "gold highlights"], decor=["menu cards", "reservation ribbon", "plate circles"], tokens={"primary":"#7f1d1d","accent":"#facc15","secondary":"#fb923c","radius":"26px"}),
        "Luxury / Real Estate": dict(name="Premium Architecture Showcase", structure="Minimal dark premium layout with architecture image dominance, elegant typography, gold linework, and site visit CTA.", hero="Large architectural image with refined dark overlay.", bg=["deep charcoal", "gold accent line", "minimal premium whitespace"], decor=["thin gold rules", "location chip", "gallery frame"], tokens={"primary":"#11100e","accent":"#d4af37","secondary":"#f8fafc","radius":"10px"}),
        "Healthcare / Clinic": dict(name="Calm Trust First", structure="Clean white/blue layout with trust strip, service benefits, calm image area, and appointment CTA.", hero="Friendly clinic/service visual with soft blue frame.", bg=["white", "calm blue wash", "soft medical shapes"], decor=["trust strip", "service cards", "appointment chip"], tokens={"primary":"#0f766e","accent":"#38bdf8","secondary":"#e0f2fe","radius":"24px"}),
        "Generic Professional": dict(name="Modern Conversion Mosaic", structure="Improved professional layout with asymmetric headline, proof strip, relevant visual, offer, and CTA.", hero="Polished product/lifestyle visual block.", bg=["indigo gradient", "soft cards", "modern mesh glow"], decor=["proof chips", "accent orbs", "benefit tiles"], tokens={"primary":"#312e81","accent":"#06b6d4","secondary":"#eef2ff","radius":"24px"}),
    }
    spec = specs[family]
    asset_notes = {
        "Poster": "Use a tall composition with clear distance-readable headline and one dominant hero moment.",
        "Banner": "Use a wide horizontal composition; keep copy short and put CTA/offer in the first scan path.",
        "Pamphlet": "Use multi-panel brochure sections with distinct cover, benefits, proof, offer, and contact panels.",
    }.get(content_type, "Keep the composition clean, responsive, and customer-facing.")
    return {
        "composition_name": spec["name"], "layout_family": family, "visual_structure": spec["structure"],
        "hero_zone": spec["hero"], "headline_zone": "Primary headline gets the largest type and strongest contrast.",
        "offer_zone": "Offer appears as a visible badge/card without exposing strategy labels.",
        "cta_zone": "CTA is a high-contrast button in the natural final scan position.",
        "trust_zone": "Use credibility proof, audience fit, mentor/family/clinic/lifestyle trust cues as relevant.",
        "benefit_zone": "Show three concise customer benefits in layout-specific cards or chips.",
        "image_zone": spec["hero"], "background_layers": spec["bg"], "decorative_elements": spec["decor"],
        "spacing_rules": ["Use generous whitespace", "Avoid repeated equal-card grids unless the family calls for it", "Keep print-safe margins"],
        "responsive_rules": ["Stack zones on small screens", "Keep CTA and offer visible above fold", "Scale headline aggressively but preserve readability"],
        "css_tokens": spec["tokens"],
        "html_sections": ["brand", "headline", "hero", "offer", "benefits", "trust", "cta"],
        "asset_specific_notes": asset_notes,
    }


def format_composition_for_prompt(composition: dict[str, Any] | None) -> str:
    if not composition:
        return "No asset composition strategy was provided."
    lines = []
    labels = {k: k.replace("_", " ").title() for k in COMPOSITION_FIELDS}
    for key in COMPOSITION_FIELDS:
        value = composition.get(key, "")
        if isinstance(value, list):
            value = "; ".join(str(v) for v in value)
        elif isinstance(value, dict):
            value = "; ".join(f"{k}: {v}" for k, v in value.items())
        lines.append(f"- {labels[key]}: {value}")
    return "\n".join(lines)
