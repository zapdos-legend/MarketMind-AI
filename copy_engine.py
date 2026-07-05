"""Marketing Copy Intelligence Engine for MarketMind-AI.

Phase 8 converts the deterministic strategy stack into polished, conversion-
focused copy while preserving the industry alignment guardrails introduced in
Phase 7.5. The engine is intentionally dependency-free and conservative: user
brief fields remain separate, additional instructions influence style only, and
forbidden industry terms are removed before the strategy is returned.
"""

from __future__ import annotations

import re
from typing import Any

SUPPORTED_INDUSTRIES = {
    "healthcare", "real_estate", "cafe_food", "fitness_app", "edtech",
    "beauty_skincare", "saas", "ecommerce", "event_promotion", "generic_business",
}

PROMPT_LEAK_PATTERNS = (
    r"\bshow\s+[^.]+", r"\binclude\s+[^.]+", r"\buse\s+[^.]+messaging\b",
    r"\bfocus\s+on\s+[^.]+", r"\badd\s+[^.]+", r"\blayout\b", r"\bvisual\b",
    r"\bcta\b", r"\bcall\s*to\s*action\b", r"\bprompt\b", r"\binstruction",
)

CTA_HINT_RE = re.compile(r"\binclude\s+([A-Za-z][A-Za-z\s&+-]{1,42}?)\s+CTA\b", re.IGNORECASE)

INDUSTRY_PROFILES: dict[str, dict[str, Any]] = {
    "healthcare": {
        "concept": "Preventive family care", "angle": "Trust, calm guidance, and one simple appointment",
        "headlines": ["Free Health Screening For Your Family", "Your Health Deserves A Simple Checkup", "Trusted Care Starts With One Appointment"],
        "sub": "A caring checkup camp with BP, sugar and BMI screening for families and seniors.",
        "benefits": ["Preventive health guidance", "Family-friendly screening", "Easy appointment booking"],
        "proof": ["Calm clinical care", "Doctor-led health guidance", "Trusted family wellness support"],
        "urgency": "Book your screening slot while camp appointments are available.",
        "trust": "Trusted care for your family, delivered with clarity and compassion.",
        "emotion": "family wellbeing", "aud_phrase": "for families and senior citizens",
        "notes": ["Use calm healthcare language.", "Frame the offer as preventive care.", "Prefer appointment CTAs."],
    },
    "real_estate": {
        "concept": "Premium lifestyle living", "angle": "Home ownership aspiration with site-visit action",
        "headlines": ["Find Your Next Premium Home", "Move Into Lifestyle-Led Living", "Experience Skyline Living First"],
        "sub": "Explore thoughtfully designed homes, premium amenities and a location made for modern families.",
        "benefits": ["Premium family living", "Modern amenities", "Prime location advantage"],
        "proof": ["Premium residential planning", "Lifestyle-focused amenities", "Site visits available"],
        "urgency": "Schedule your site visit before priority viewing slots fill up.",
        "trust": "A polished address designed around comfort, convenience and everyday pride.",
        "emotion": "home aspiration", "aud_phrase": "for modern home buyers",
        "notes": ["Use premium property language.", "Connect amenities to family lifestyle.", "Prefer site-visit CTAs."],
    },
    "cafe_food": {
        "concept": "Better morning ritual", "angle": "Fresh breakfast value for busy workdays",
        "headlines": ["Coffee & Breakfast For A Better Morning", "Start Your Workday Fresh", "Your Morning Combo, Made Fresh"],
        "sub": "Fresh coffee and a satisfying breakfast bite made quick, warm and office-ready.",
        "benefits": ["Fresh morning combo", "Quick workday fuel", "Warm café comfort"],
        "proof": ["Freshly served every morning", "Office-ready breakfast value", "Cozy café experience"],
        "urgency": "Visit today and make your morning break feel worth it.",
        "trust": "Freshly made café favorites served with warm, friendly energy.",
        "emotion": "morning comfort", "aud_phrase": "for busy office workers",
        "notes": ["Use appetite-driven language.", "Keep notes out of offer text.", "Only mention pizza if explicitly requested."],
    },
    "fitness_app": {
        "concept": "Campus fitness momentum", "angle": "Student-friendly tracking, streaks and motivation",
        "headlines": ["Fitness Made For College Life", "Track Workouts. Build Streaks.", "Your 7-Day Fitness Kickstart"],
        "sub": "A fitness app that helps students track workouts, build streaks and stay moving.",
        "benefits": ["Workout progress tracking", "Student-friendly routines", "Motivating fitness streaks"],
        "proof": ["Built for active student schedules", "Progress tracking that keeps momentum visible", "Simple app-based fitness habits"],
        "urgency": "Start your free trial and build your first week of momentum.",
        "trust": "Designed for students who want fitness to fit real campus life.",
        "emotion": "personal momentum", "aud_phrase": "for college students",
        "notes": ["Use energetic app launch copy.", "Mention tracking and streaks.", "Prefer download or trial CTAs."],
    },
    "edtech": {
        "concept": "Career-ready skill growth", "angle": "Mentor-led AI learning with projects and credentials",
        "headlines": ["Build Job-Ready AI Skills Faster", "Launch Your Data Science Career", "Learn AI. Build Projects."],
        "sub": "Gain AI and data science skills through mentorship, projects, certification and a clear learning roadmap.",
        "benefits": ["Mentor-led learning", "Hands-on AI projects", "Certificate-backed career growth"],
        "proof": ["Project-based learning roadmap", "Mentor guidance included", "Certificate credibility for career growth"],
        "urgency": "Apply early to unlock scholarship consideration before seats move fast.",
        "trust": "A structured path for ambitious learners building future-ready AI skills.",
        "emotion": "career confidence", "aud_phrase": "for students and fresh graduates",
        "notes": ["Use career transformation language.", "Mention AI/data science when relevant.", "Avoid exam-prep framing unless explicitly requested."],
    },
    "beauty_skincare": {"concept":"Confident glow","angle":"Premium care with visible everyday confidence","headlines":["Glow With Confidence Every Day","Your Skin Deserves Premium Care","Start A Softer Glow Ritual"],"sub":"A polished beauty experience made for simple routines and visible confidence.","benefits":["Visible glow","Premium care","Easy routine"],"proof":["Skin-first care","Premium beauty experience","Soft, reassuring guidance"],"urgency":"Book or shop today while launch availability is open.","trust":"Premium care for a confident everyday glow.","emotion":"self-confidence","aud_phrase":"for beauty-conscious customers","notes":["Use elegant beauty language."]},
    "saas": {"concept":"Workflow clarity","angle":"Modern software value with fast activation","headlines":["Simplify Workflows With Smarter Software","See Your Team Work Clearly","Start Faster With Better Visibility"],"sub":"A modern platform that helps teams save time, simplify work and act with confidence.","benefits":["Save time","Simplify workflows","Improve visibility"],"proof":["Modern dashboard experience","Workflow automation","Clear team visibility"],"urgency":"Start today and see a faster workflow in action.","trust":"Built for teams that need clarity without extra complexity.","emotion":"control","aud_phrase":"for modern teams","notes":["Use clear SaaS language."]},
    "ecommerce": {"concept":"Easy shopping value","angle":"Product-led offer with fast purchase action","headlines":["Shop The Offer Before It Goes","Fresh Finds, Easy Checkout","Claim Better Value Today"],"sub":"Discover useful products, clear savings and a simple shopping path.","benefits":["Easy shopping","Great offers","Fast checkout"],"proof":["Product-focused value","Simple shopping experience","Offer-led discovery"],"urgency":"Claim the offer before availability changes.","trust":"A simple shopping experience built around clear value.","emotion":"smart buying","aud_phrase":"for online shoppers","notes":["Use shopping-focused copy."]},
    "event_promotion": {"concept":"Live moment urgency","angle":"Registration-led event value","headlines":["Reserve Your Spot For The Event","Join The Moment Live","Don’t Miss The Next Big Session"],"sub":"A timely experience with valuable takeaways, limited seats and a clear reason to register.","benefits":["Live experience","Limited seats","Valuable networking"],"proof":["Event-ready programming","Timely registration", "Clear attendee value"],"urgency":"Register before seats are gone.","trust":"A well-planned event experience with clear takeaways.","emotion":"anticipation","aud_phrase":"for attendees","notes":["Use event urgency."]},
    "generic_business": {"concept":"Clear customer value","angle":"Benefit-led message with one easy next step","headlines":["A Smarter Reason To Choose Us","Clear Value. Simple Next Step.","Make Your Next Move Easier"],"sub":"A practical offer built around customer needs, trust and easy action.","benefits":["Clear value","Trusted experience","Simple next step"],"proof":["Customer-first experience","Practical service details","Clear next step"],"urgency":"Take the next step while the offer is available.","trust":"Trusted support for customers who want clarity before they act.","emotion":"confidence","aud_phrase":"for your ideal customers","notes":["Keep copy concrete and customer-first."]},
}


def clean_string(value: Any, default: str = "") -> str:
    """Return trimmed text while preserving punctuation and symbols such as ₹."""
    cleaned = re.sub(r"\s+", " ", str(value or "")).strip()
    return cleaned or default


def split_user_notes_from_offer(offer: str, notes: str = "") -> tuple[str, str]:
    """Separate accidental offer+instruction concatenation without destroying symbols."""
    offer = clean_string(offer)
    notes = clean_string(notes)
    markers = ["Show ", "Use ", "Include ", "Focus ", "Add "]
    for marker in markers:
        idx = offer.find(marker)
        if idx > 0:
            leaked = offer[idx:].strip()
            offer = offer[:idx].strip()
            notes = clean_string(f"{notes} {leaked}" if notes else leaked)
            break
    return offer, notes


def normalize_form_data(form_data: dict[str, Any] | None) -> dict[str, str]:
    """Support legacy and current form field names with offer/notes separation."""
    data = form_data if isinstance(form_data, dict) else {}
    normalized = {
        "content_type": clean_string(data.get("content_type") or data.get("asset_type"), "Marketing Text"),
        "topic": clean_string(data.get("topic") or data.get("main_prompt") or data.get("prompt")),
        "business_name": clean_string(data.get("business_name")),
        "product_service": clean_string(data.get("product_service") or data.get("product")),
        "audience": clean_string(data.get("audience") or data.get("target_audience")),
        "platform": clean_string(data.get("platform")),
        "tone": clean_string(data.get("tone")),
        "offer": clean_string(data.get("offer")),
        "notes": clean_string(data.get("notes") or data.get("additional_instructions")),
    }
    normalized["offer"], normalized["notes"] = split_user_notes_from_offer(normalized["offer"], normalized["notes"])
    return normalized


def _extract_cta_from_notes(notes: str) -> str:
    match = CTA_HINT_RE.search(notes or "")
    return clean_string(match.group(1)) if match else ""


def prevent_prompt_leakage(text: str) -> str:
    """Remove instruction-like fragments from customer-facing copy."""
    fixed = clean_string(text)
    for pattern in PROMPT_LEAK_PATTERNS:
        fixed = re.sub(pattern, "", fixed, flags=re.IGNORECASE).strip(" .;:-")
    return clean_string(fixed)


def _word_limit(text: str, limit: int) -> str:
    words = text.split()
    return text if len(words) <= limit else " ".join(words[:limit]).rstrip(" ,;:")


def limit_headline_length(text: str, asset_type: str) -> str:
    """Apply preferred visual-asset headline limits."""
    limit = 7 if asset_type == "Banner" else 8 if asset_type == "Poster" else 12
    return _word_limit(text, limit)


def _clean_list(items: list[str], forbidden_terms: list[str], warnings: list[str], limit: int) -> list[str]:
    cleaned: list[str] = []
    for item in items:
        safe = validate_against_forbidden_terms(prevent_prompt_leakage(item), forbidden_terms, warnings)
        if safe and safe not in cleaned:
            cleaned.append(safe)
        if len(cleaned) >= limit:
            break
    return cleaned


def validate_against_forbidden_terms(text: str, forbidden_terms: list[str], warnings: list[str] | None = None) -> str:
    """Remove forbidden industry terms from a string and record warnings."""
    fixed = clean_string(text)
    for term in forbidden_terms or []:
        term = clean_string(term)
        if not term:
            continue
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        if pattern.search(fixed):
            fixed = pattern.sub("", fixed)
            if warnings is not None:
                warnings.append(f"Removed forbidden copy term '{term}'.")
    return clean_string(re.sub(r"\s{2,}", " ", fixed).strip(" ,;:-"))


def _choose_offer_line(offer: str, profile: dict[str, Any], forbidden: list[str], warnings: list[str]) -> str:
    cleaned = validate_against_forbidden_terms(prevent_prompt_leakage(offer), forbidden, warnings)
    return cleaned or "Ask about current availability and packages"


def _choose_cta(form: dict[str, str], alignment: dict[str, Any], profile: dict[str, Any]) -> tuple[str, str]:
    hint = _extract_cta_from_notes(form.get("notes", ""))
    recommended = [clean_string(cta) for cta in alignment.get("recommended_ctas", []) if clean_string(cta)]
    primary = hint or (recommended[0] if recommended else "Get Started")
    secondary = recommended[1] if len(recommended) > 1 else ("Learn More" if primary != "Learn More" else "Contact Us")
    return primary, secondary


def _contextual_headline(industry: str, form: dict[str, str], profile: dict[str, Any]) -> str:
    text = f"{form.get('topic')} {form.get('product_service')} {form.get('offer')}".lower()
    if industry == "cafe_food" and "coffee" in text and "breakfast" in text:
        return "Coffee & Breakfast For A Better Morning"
    if industry == "edtech" and ("ai" in text or "data science" in text):
        return "Build Job-Ready AI Skills Faster"
    if industry == "healthcare" and ("screen" in text or "checkup" in text):
        return "Free Health Screening For Your Family"
    if industry == "real_estate" and ("apartment" in text or "home" in text):
        return "Find Your Next Premium Home"
    if industry == "fitness_app" and ("college" in text or "student" in text):
        return "Fitness Made For College Life"
    return profile["headlines"][0]


def generate_copy_strategy(form_data: dict[str, Any] | None, campaign_strategy: dict[str, Any] | None = None, creative_strategy: dict[str, Any] | None = None, design_strategy: dict[str, Any] | None = None, asset_composition: dict[str, Any] | None = None, visual_components: dict[str, Any] | None = None, industry_alignment: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return an industry-aware conversion copy strategy for downstream use."""
    form = normalize_form_data(form_data)
    alignment = industry_alignment or {}
    industry = clean_string(alignment.get("detected_industry"), "generic_business")
    if industry not in SUPPORTED_INDUSTRIES:
        industry = "generic_business"
    profile = INDUSTRY_PROFILES[industry]
    forbidden = [clean_string(item) for item in alignment.get("forbidden_terms", [])]
    warnings: list[str] = []
    asset_type = form.get("content_type", "Marketing Text")

    headline = _contextual_headline(industry, form, profile)
    headline = limit_headline_length(validate_against_forbidden_terms(prevent_prompt_leakage(headline), forbidden, warnings), asset_type)
    sub_limit = 14 if asset_type == "Banner" else 18 if asset_type == "Poster" else 28
    subheadline = _word_limit(validate_against_forbidden_terms(prevent_prompt_leakage(profile["sub"]), forbidden, warnings), sub_limit)
    bullet_limit = 5 if asset_type == "Pamphlet" else 3
    primary_cta, secondary_cta = _choose_cta(form, alignment, profile)
    primary_cta = validate_against_forbidden_terms(prevent_prompt_leakage(primary_cta), forbidden, warnings)
    secondary_cta = validate_against_forbidden_terms(prevent_prompt_leakage(secondary_cta), forbidden, warnings)
    offer_line = _choose_offer_line(form.get("offer", ""), profile, forbidden, warnings)

    strategy = {
        "detected_industry": industry,
        "detected_sub_industry": clean_string(alignment.get("detected_sub_industry")),
        "business_name": form.get("business_name", ""),
        "product_service": form.get("product_service", ""),
        "copy_concept": profile["concept"],
        "copy_angle": profile["angle"],
        "primary_headline": headline,
        "alternate_headlines": _clean_list(profile["headlines"][1:] + [headline], forbidden, warnings, 3),
        "subheadline": subheadline,
        "benefit_bullets": _clean_list(list(alignment.get("recommended_benefits", [])) + profile["benefits"], forbidden, warnings, bullet_limit),
        "proof_points": _clean_list(profile["proof"], forbidden, warnings, 3),
        "offer_line": offer_line,
        "urgency_line": validate_against_forbidden_terms(prevent_prompt_leakage(profile["urgency"]), forbidden, warnings),
        "cta_primary": primary_cta,
        "cta_secondary": secondary_cta,
        "microcopy": f"{secondary_cta} if you need details before deciding.",
        "trust_line": validate_against_forbidden_terms(prevent_prompt_leakage(profile["trust"]), forbidden, warnings),
        "emotional_trigger": profile["emotion"],
        "audience_specific_phrase": form.get("audience") or profile["aud_phrase"],
        "industry_copy_notes": list(profile["notes"]),
        "forbidden_copy_warnings": [],
    }
    # Final pass over every generated field.
    for key, value in list(strategy.items()):
        if isinstance(value, str) and key not in {"detected_industry", "detected_sub_industry", "business_name", "product_service"}:
            strategy[key] = validate_against_forbidden_terms(prevent_prompt_leakage(value), forbidden, warnings)
        elif isinstance(value, list):
            strategy[key] = _clean_list([str(item) for item in value], forbidden, warnings, len(value))
    strategy["forbidden_copy_warnings"] = sorted(set(warnings))
    return strategy


def format_copy_for_prompt(copy_strategy: dict[str, Any] | None) -> str:
    """Format copy strategy for prompt_builder high-priority instructions."""
    if not copy_strategy:
        return "No marketing copy intelligence was provided."
    labels = {
        "copy_concept":"Copy Concept", "copy_angle":"Copy Angle", "primary_headline":"Primary Headline",
        "alternate_headlines":"Alternate Headlines", "subheadline":"Subheadline", "benefit_bullets":"Benefit Bullets",
        "proof_points":"Proof Points", "offer_line":"Offer Line", "urgency_line":"Urgency Line",
        "cta_primary":"Primary CTA", "cta_secondary":"Secondary CTA", "microcopy":"Microcopy", "trust_line":"Trust Line",
        "emotional_trigger":"Emotional Trigger", "audience_specific_phrase":"Audience Phrase", "industry_copy_notes":"Industry Copy Notes",
        "forbidden_copy_warnings":"Forbidden Copy Warnings",
    }
    lines = []
    for key, label in labels.items():
        value = copy_strategy.get(key, "")
        if isinstance(value, list):
            value = "; ".join(str(item) for item in value)
        lines.append(f"- {label}: {value}")
    return "\n".join(lines)
