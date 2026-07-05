"""Industry Intelligence & Semantic Alignment Engine for MarketMind-AI.

Phase 7.5 locks the user's business context before downstream strategy,
creative, design, composition, visual component, prompt, and AI fallback layers
run. The engine is deterministic and intentionally conservative: product/service
and main prompt signals outweigh broad audience words so healthcare campaigns do
not become fitness campaigns, real estate does not become food, and café offers
remain café offers unless pizza is explicitly requested.
"""

from __future__ import annotations

import copy
import re
from typing import Any

FIELDS = (
    "detected_industry", "detected_sub_industry", "confidence_score",
    "business_context_summary", "product_context_summary", "audience_context_summary",
    "offer_context_summary", "campaign_intent", "allowed_terms", "forbidden_terms",
    "allowed_imagery", "forbidden_imagery", "recommended_ctas", "forbidden_ctas",
    "recommended_benefits", "forbidden_benefits", "tone_guidelines",
    "visual_guidelines", "copy_guardrails", "semantic_warnings",
    "downstream_instructions",
)

INDUSTRIES: dict[str, dict[str, Any]] = {
    "healthcare": {
        "sub": "clinic / preventive care", "terms": ["doctor", "clinic", "health checkup", "family wellness", "appointment", "preventive care", "medical", "trusted care"],
        "forbidden": ["workout", "fitness streak", "calorie tracking", "gym", "pizza", "luxury apartment", "download app"],
        "imagery": ["doctor", "clinic", "family wellness", "medical card", "appointment card", "calm healthcare layout"],
        "bad_imagery": ["gym", "athlete", "pizza", "food table", "apartment towers", "fitness app UI"],
        "ctas": ["Book Appointment", "Schedule Checkup", "Reserve Health Checkup"],
        "bad_ctas": ["Download App", "Order Now", "Book Site Visit", "Start Workout"],
        "benefits": ["Trusted care for your family", "Preventive health guidance", "Easy appointment booking"],
        "bad_benefits": ["Quick workouts", "Fitness streaks", "Pizza deals", "Premium apartment amenities"],
        "tone": "Trustworthy, calm, credible, caring, and family-first.",
        "visual": "Use clean white/aqua/blue healthcare styling, doctor or clinic cues, service cards, credibility badges, and appointment CTA blocks.",
    },
    "real_estate": {
        "sub": "residential property", "terms": ["premium living", "apartments", "amenities", "site visit", "location", "architecture", "residences", "property"],
        "forbidden": ["pizza", "coffee", "workout", "medical checkup", "download app", "clinic", "sandwich"],
        "imagery": ["luxury architecture", "apartments", "premium interiors", "amenity grid", "location pin", "site visit badge"],
        "bad_imagery": ["pizza", "coffee", "restaurant table", "gym workout", "doctor clinic", "app dashboard"],
        "ctas": ["Book Site Visit", "Schedule Visit", "Reserve Your Tour"],
        "bad_ctas": ["Order Now", "Download App", "Book Appointment", "Start Free Trial"],
        "benefits": ["Premium living designed for modern professionals", "Exclusive amenities", "Prime location advantage"],
        "bad_benefits": ["Fresh food", "Quick workouts", "Medical checkups", "Workflow automation"],
        "tone": "Premium, elegant, aspirational, polished, and exclusive.",
        "visual": "Use dark premium styling, gold accents, architecture visuals, amenity grids, property highlights, and site visit CTAs.",
    },
    "cafe_food": {
        "sub": "café / breakfast combo", "terms": ["coffee", "café", "cafe", "sandwich", "breakfast", "morning", "fresh", "quick bite", "combo"],
        "forbidden": ["pizza", "gym", "apartment", "doctor", "AI workshop", "calorie tracking", "site visit"],
        "imagery": ["coffee", "sandwich", "breakfast", "cozy café", "morning light", "price badge"],
        "bad_imagery": ["pizza", "gym", "apartment tower", "doctor", "classroom", "software dashboard"],
        "ctas": ["Order Now", "Grab Breakfast", "Visit Today"],
        "bad_ctas": ["Download App", "Book Site Visit", "Book Appointment", "Register Now"],
        "benefits": ["Fresh coffee and sandwich combo", "Quick affordable morning start", "Office-ready breakfast"],
        "bad_benefits": ["Family dinner", "Workout streaks", "Luxury amenities", "AI skills roadmap"],
        "tone": "Warm, cozy, appetizing, energetic for mornings, and local.",
        "visual": "Use warm coffee browns, cream, gold, breakfast imagery, combo card, menu chips, review card, and opening-hours strip.",
    },
    "restaurant": {
        "sub": "restaurant / dining", "terms": ["restaurant", "dining", "menu", "reservation", "chef", "meal", "family dinner"],
        "forbidden": ["gym", "apartment", "doctor", "AI workshop", "software workflow"],
        "imagery": ["restaurant table", "chef special", "menu", "family dining"], "bad_imagery": ["gym", "clinic", "apartment tower", "classroom"],
        "ctas": ["Reserve Table", "Order Now", "Visit Tonight"], "bad_ctas": ["Download App", "Book Site Visit"],
        "benefits": ["Fresh dining experience", "Chef-led menu", "Easy reservation"], "bad_benefits": ["Workout streaks", "Premium apartments"],
        "tone": "Warm, appetizing, hospitable.", "visual": "Use food/table/menu visuals with warm restaurant styling.",
    },
    "fitness_app": {"sub":"fitness mobile app","terms":["fitness app","workout","gym app","healthy habits","progress tracking","streak","training"],"forbidden":["pizza","apartment","clinic","doctor","site visit","AI workshop"],"imagery":["workout","app UI","student fitness","athlete","phone mockup","progress cards"],"bad_imagery":["pizza","clinic","apartment","coffee shop","classroom"],"ctas":["Start Free Trial","Download App","Try FitRush Today"],"bad_ctas":["Order Now","Book Site Visit","Book Appointment"],"benefits":["Quick workouts","Progress tracking","Healthy habits"],"bad_benefits":["Pizza deals","Luxury amenities","Medical checkups"],"tone":"Energetic, motivational, social, and action-oriented.","visual":"Use athlete imagery, fitness tracking UI, phone mockup, progress streaks, workout stats, challenge badges, and neon accents."},
    "edtech": {"sub":"course / workshop","terms":["course","workshop","training","bootcamp","learning","students","mentor","certificate","AI skills"],"forbidden":["gym","pizza","apartment","clinic","doctor","coffee combo"],"imagery":["learning","course card","skills roadmap","mentor","certificate","progress bars"],"bad_imagery":["gym","pizza","apartment tower","clinic bed"],"ctas":["Register Now","Join Workshop","Reserve Seat"],"bad_ctas":["Order Now","Book Site Visit","Book Appointment"],"benefits":["Career-ready skills","Mentor-led learning","Certificate credibility"],"bad_benefits":["Quick workouts","Pizza combos","Luxury amenities"],"tone":"Professional, credible, encouraging, and future-ready.","visual":"Use learning/course/skills visuals, mentor credibility, certificates, progress bars, and registration urgency."},
    "beauty_skincare": {"sub":"beauty / skincare","terms":["beauty","skincare","glow","salon","skin","cosmetic"],"forbidden":["gym","pizza","apartment","clinic checkup"],"imagery":["glow","skincare product","beauty routine","soft lighting"],"bad_imagery":["gym","pizza","architecture"],"ctas":["Shop Now","Book Consultation","Glow Today"],"bad_ctas":["Download App","Book Site Visit"],"benefits":["Visible glow","Premium care","Easy routine"],"bad_benefits":["Workout streaks","Apartment amenities"],"tone":"Premium, reassuring, elegant.","visual":"Use blush, cream, soft gradients, product/service closeups, and trust cues."},
    "saas": {"sub":"software / SaaS","terms":["software","saas","dashboard","workflow","automation","platform"],"forbidden":["pizza","doctor","apartment","gym workout"],"imagery":["dashboard","workflow","software UI","team productivity"],"bad_imagery":["pizza","clinic","apartment tower"],"ctas":["Start Free Trial","Book Demo","Get Started"],"bad_ctas":["Order Now","Book Site Visit"],"benefits":["Save time","Simplify workflows","Improve visibility"],"bad_benefits":["Fresh breakfast","Medical checkups"],"tone":"Clear, modern, benefit-led.","visual":"Use dashboard, product UI, clean digital gradients, and proof cards."},
    "ecommerce": {"sub":"online store","terms":["shop","store","ecommerce","product","sale","cart"],"forbidden":["doctor","apartment","gym workout"],"imagery":["products","shopping cards","offer badge"],"bad_imagery":["clinic","apartment"],"ctas":["Shop Now","Buy Now","Claim Offer"],"bad_ctas":["Book Site Visit"],"benefits":["Easy shopping","Great offers","Fast checkout"],"bad_benefits":["Medical checkups"],"tone":"Direct, persuasive, shopping-focused.","visual":"Use product-focused imagery, price badges, and checkout cues."},
    "event_promotion": {"sub":"event promotion","terms":["event","conference","webinar","festival","registration"],"forbidden":["pizza deal","apartment amenities","clinic checkup"],"imagery":["stage","speaker","calendar","registration badge"],"bad_imagery":["pizza","clinic","apartment"],"ctas":["Register Now","Reserve Spot","Join Event"],"bad_ctas":["Order Now","Book Site Visit"],"benefits":["Live experience","Limited seats","Valuable networking"],"bad_benefits":["Pizza combos"],"tone":"Exciting, urgent, clear.","visual":"Use event date, speaker, venue, and registration components."},
    "generic_business": {"sub":"general business","terms":["customers","offer","service","trusted","value"],"forbidden":[],"imagery":["brand-relevant lifestyle","product/service cue","proof cards"],"bad_imagery":[],"ctas":["Get Started","Contact Us","Claim Offer"],"bad_ctas":[],"benefits":["Clear value","Trusted experience","Simple next step"],"bad_benefits":[],"tone":"Clear, persuasive, customer-first.","visual":"Use polished brand-relevant visuals and conversion cards."},
}

KEYWORDS = {
    "healthcare": ["health checkup", "clinic", "doctor", "medical", "hospital", "healthcare", "appointment", "checkup camp"],
    "real_estate": ["luxury apartment", "apartment", "residence", "residences", "property", "real estate", "site visit", "premium living"],
    "cafe_food": ["coffee", "café", "cafe", "sandwich", "breakfast", "quick bite", "morning combo"],
    "fitness_app": ["fitness app", "gym app", "workout app", "workout", "fitness tracking", "fitrush"],
    "edtech": ["ai workshop", "course", "training", "bootcamp", "edtech", "learning", "career workshop", "skillforge"],
    "restaurant": ["restaurant", "dining", "reservation", "chef", "dinner", "meal"],
    "beauty_skincare": ["beauty", "skincare", "skin", "glow", "salon", "cosmetic"],
    "saas": ["saas", "software", "dashboard", "workflow", "automation", "platform"],
    "ecommerce": ["ecommerce", "shop", "online store", "cart", "buy now"],
    "event_promotion": ["event", "conference", "webinar", "festival", "registration"],
}

REPLACEMENTS = {
    "healthcare": {"workout":"checkup", "fitness":"wellness", "gym":"clinic", "calorie tracking":"preventive care", "download app":"book appointment", "pizza":"health checkup", "luxury apartment":"trusted clinic"},
    "real_estate": {"pizza":"apartments", "food":"amenities", "coffee":"premium living", "workout":"lifestyle", "medical checkup":"site visit", "download app":"book site visit", "clinic":"residence"},
    "cafe_food": {"pizza":"coffee and sandwich", "gym":"café", "apartment":"breakfast", "doctor":"barista", "AI workshop":"morning combo"},
}


def _clean(value: Any, default: str = "") -> str:
    return " ".join(str(value or "").split()) or default


def _weighted_blob(form_data: dict[str, Any]) -> list[tuple[str, int]]:
    return [
        (_clean(form_data.get("product_service")).lower(), 5),
        (_clean(form_data.get("topic")).lower(), 4),
        (_clean(form_data.get("business_name")).lower(), 3),
        (_clean(form_data.get("offer")).lower(), 3),
        (_clean(form_data.get("notes")).lower(), 2),
        (_clean(form_data.get("tone")).lower(), 1),
        (_clean(form_data.get("platform")).lower(), 1),
        (_clean(form_data.get("audience")).lower(), 1),
    ]


def detect_industry(form_data: dict[str, Any]) -> tuple[str, float, list[str]]:
    scores = {name: 0 for name in INDUSTRIES if name != "generic_business"}
    hits: list[str] = []
    for text, weight in _weighted_blob(form_data):
        for industry, keywords in KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    scores[industry] += weight * (2 if " " in keyword else 1)
                    hits.append(f"{industry}:{keyword}")
    # Health alone is ambiguous; don't let audience-level health overpower exact clinic/checkup signals already covered.
    best, score = max(scores.items(), key=lambda item: item[1])
    if score <= 0:
        return "generic_business", 0.45, []
    confidence = min(0.98, 0.55 + (score / 30))
    return best, round(confidence, 2), hits


def build_industry_alignment(form_data: dict[str, Any]) -> dict[str, Any]:
    """Return a complete semantic alignment dictionary for downstream engines."""
    form_data = form_data if isinstance(form_data, dict) else {}
    industry, confidence, hits = detect_industry(form_data)
    spec = INDUSTRIES[industry]
    business = _clean(form_data.get("business_name"), "the business")
    product = _clean(form_data.get("product_service"), _clean(form_data.get("topic"), "the offer"))
    audience = _clean(form_data.get("audience"), "the intended audience")
    offer = _clean(form_data.get("offer"), "the campaign offer")
    intent = _clean(form_data.get("topic"), f"Promote {product}")
    warnings = [] if hits else ["No strong industry keyword match; using generic business guardrails."]
    return {
        "detected_industry": industry,
        "detected_sub_industry": spec["sub"],
        "confidence_score": confidence,
        "business_context_summary": f"{business} should be presented only in the context of {industry.replace('_', ' ')}.",
        "product_context_summary": f"Keep {product} central; do not substitute unrelated products or services.",
        "audience_context_summary": f"Speak to {audience} without letting audience words override the product/service category.",
        "offer_context_summary": f"Use the offer '{offer}' only in a {industry.replace('_', ' ')} context.",
        "campaign_intent": intent,
        "allowed_terms": list(spec["terms"]),
        "forbidden_terms": list(spec["forbidden"]),
        "allowed_imagery": list(spec["imagery"]),
        "forbidden_imagery": list(spec["bad_imagery"]),
        "recommended_ctas": list(spec["ctas"]),
        "forbidden_ctas": list(spec["bad_ctas"]),
        "recommended_benefits": list(spec["benefits"]),
        "forbidden_benefits": list(spec["bad_benefits"]),
        "tone_guidelines": spec["tone"],
        "visual_guidelines": spec["visual"],
        "copy_guardrails": [
            "Preserve the exact product/service context from the user brief.",
            "Prefer allowed terms and recommended benefits before generic defaults.",
            "Never introduce forbidden terms, CTAs, benefits, or imagery unless explicitly present in product/service.",
            "Do not drift into unrelated industries even if generic audience words overlap.",
        ],
        "semantic_warnings": warnings,
        "downstream_instructions": f"All downstream engines must treat {industry} as the semantic source of truth and use {', '.join(spec['ctas'][:2])} style CTAs.",
    }


def format_industry_for_prompt(alignment: dict[str, Any] | None) -> str:
    if not alignment:
        return "No industry alignment was provided."
    labels = {key: key.replace("_", " ").title() for key in FIELDS}
    lines = []
    for key in FIELDS:
        value = alignment.get(key, "")
        if isinstance(value, list):
            value = "; ".join(str(v) for v in value)
        lines.append(f"- {labels[key]}: {value}")
    return "\n".join(lines)


def _replace_text(text: str, alignment: dict[str, Any], warnings: list[str]) -> str:
    industry = alignment.get("detected_industry", "generic_business")
    replacements = REPLACEMENTS.get(industry, {})
    fixed = text
    for term in alignment.get("forbidden_terms", []):
        if not term:
            continue
        pattern = re.compile(re.escape(str(term)), re.IGNORECASE)
        if pattern.search(fixed):
            replacement = replacements.get(str(term).lower()) or (alignment.get("allowed_terms") or ["customer value"])[0]
            fixed = pattern.sub(str(replacement), fixed)
            warnings.append(f"Replaced forbidden term '{term}' with '{replacement}'.")
    return fixed


def validate_semantic_alignment(output: Any, industry_alignment: dict[str, Any] | None) -> Any:
    """Remove/replace forbidden terms inside generated dictionaries or strings."""
    if not industry_alignment:
        return output
    warnings = industry_alignment.setdefault("semantic_warnings", [])
    if isinstance(output, str):
        return _replace_text(output, industry_alignment, warnings)
    if isinstance(output, list):
        return [validate_semantic_alignment(item, industry_alignment) for item in output]
    if isinstance(output, dict):
        fixed = {}
        for key, value in output.items():
            fixed[key] = validate_semantic_alignment(value, industry_alignment)
        return fixed
    return output
