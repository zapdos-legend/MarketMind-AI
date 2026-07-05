"""Campaign intelligence helpers for MarketMind-AI.

This module is the strategic layer that turns a raw user brief into a reusable
campaign strategy before any prompt or asset copy is generated.  It is designed
as a deterministic foundation today and keeps its output structured so a future
agent mode can orchestrate assets, offers, and channel recommendations from the
same campaign plan.
"""

from __future__ import annotations

import re
from typing import Any

import industry_engine

STRATEGY_FIELDS = (
    "campaign_objective",
    "target_audience",
    "audience_pain_points",
    "value_proposition",
    "key_marketing_message",
    "offer_strategy",
    "recommended_tone",
    "primary_cta",
    "recommended_channels",
    "campaign_summary",
)


def _clean(value: Any, default: str = "") -> str:
    cleaned = " ".join(str(value or "").split())
    return cleaned or default


def _combined(form_data: dict[str, Any]) -> str:
    return " ".join(_clean(form_data.get(k)) for k in ("topic", "business_name", "product_service", "audience", "platform", "tone", "offer", "notes")).lower()


def _category(text: str) -> str:
    if any(w in text for w in ("pizza", "restaurant", "cafe", "coffee", "food", "meal", "delivery")):
        return "food"
    if any(w in text for w in ("fitness", "gym", "workout", "health", "exercise")):
        return "fitness"
    if any(w in text for w in ("iit", "jee", "coaching", "academy", "class", "student", "college", "education", "course")):
        return "education"
    if any(w in text for w in ("skin", "skincare", "beauty", "cosmetic", "glow")):
        return "beauty"
    if any(w in text for w in ("app", "software", "saas", "ai", "platform", "dashboard", "technology")):
        return "technology"
    return "general"


def _infer_objective(topic: str, text: str, category: str) -> str:
    if category == "healthcare":
        return "Drive health checkup appointments and trusted community care participation"
    if category == "real_estate":
        return "Generate qualified site visit bookings for the property campaign"
    if category == "event":
        return "Generate registrations and attendance intent for the event"
    if "weekend" in text and category == "food":
        return "Increase weekend orders and in-store sales"
    if "launch" in text and ("app" in text or category == "technology"):
        return "Drive awareness, sign-ups, and product adoption for the launch"
    if "download" in text or "app" in text:
        return "Increase app downloads and active users"
    if "sale" in text or "sales" in text or "customers" in text:
        return "Increase qualified customer demand and conversions"
    if category == "education":
        return "Generate student inquiries and enrollments"
    return f"Turn interest in {topic} into measurable customer action"


def _infer_audience(form_data: dict[str, Any], text: str, category: str) -> str:
    provided = _clean(form_data.get("audience"))
    if provided:
        return provided
    if "college" in text or "student" in text:
        return "College students and young adults"
    if "family" in text or category == "food":
        return "Families, students, and local weekend buyers"
    if category == "fitness":
        return "Busy health-conscious people who want simple routines"
    if category == "beauty":
        return "Beauty-conscious shoppers looking for visible results"
    if category == "education":
        return "Ambitious students and parents comparing learning options"
    if category == "technology":
        return "Digitally savvy users looking for faster, simpler solutions"
    return "Potential customers most likely to need this offer now"


def _pain_points(category: str, text: str) -> list[str]:
    if category == "food":
        return ["Expensive dining choices", "Weekend meal indecision", "Slow or unreliable delivery"]
    if category == "fitness":
        return ["Lack of time", "Low motivation", "Inconsistent workout habits"]
    if category == "education":
        return ["Exam pressure", "Unclear study plans", "Need for trusted guidance"]
    if category == "beauty":
        return ["Confusing product choices", "Inconsistent results", "Need for trustworthy ingredients"]
    if category == "technology":
        return ["Wasted time", "Manual workflows", "Hard-to-use tools"]
    return ["Unclear value", "Too many alternatives", "Need for a simple next step"]


def _offer(form_data: dict[str, Any], category: str, text: str) -> str:
    provided = _clean(form_data.get("offer"))
    if provided:
        return provided
    pct = re.search(r"\b\d+%\s*off\b[^,.!]*", text, re.I)
    if pct:
        return pct.group(0).title()
    if "trial" in text or ("app" in text and category in {"fitness", "technology"}):
        return "7-Day Free Trial"
    if "weekend" in text and category == "food":
        return "50% Off Weekend Special"
    if category == "education":
        return "Free Demo Class"
    return "Limited-time launch incentive"


def _cta(category: str, text: str, offer: str) -> str:
    combined = f"{text} {offer}".lower()
    if "trial" in combined:
        return "Start Your Free Trial"
    if "demo" in combined:
        return "Book Your Free Demo"
    if category == "food":
        return "Order Now"
    if category == "beauty":
        return "Shop Now"
    if "download" in combined or "app" in combined:
        return "Download Now"
    return "Get Started Today"


def build_campaign_strategy(form_data: dict[str, Any], industry_alignment: dict[str, Any] | None = None) -> dict[str, Any]:
    """Infer a complete campaign strategy from the submitted user brief."""
    if not isinstance(form_data, dict):
        form_data = {}
    topic = _clean(form_data.get("topic"), "the submitted marketing request")
    text = _combined(form_data)
    alignment = industry_alignment or industry_engine.build_industry_alignment(form_data)
    industry = alignment.get("detected_industry", "generic_business")
    category_map = {"cafe_food": "food", "restaurant": "food", "fitness_app": "fitness", "edtech": "education", "beauty_skincare": "beauty", "saas": "technology", "ecommerce": "technology", "healthcare": "healthcare", "real_estate": "real_estate", "event_promotion": "event"}
    category = category_map.get(industry, _category(text))
    audience = _infer_audience(form_data, text, category)
    pains = _pain_points(category, text)
    offer = _offer(form_data, category, text)
    cta = (alignment.get("recommended_ctas") or [])[0] if industry in {"healthcare", "real_estate", "cafe_food", "fitness_app", "edtech"} else _cta(category, text, offer)
    tone = _clean(form_data.get("tone")) or {
        "food": "Warm, urgent, and appetizing",
        "fitness": "Energetic and motivational",
        "education": "Encouraging, credible, and aspirational",
        "beauty": "Premium, confident, and reassuring",
        "technology": "Clear, modern, and benefit-led",
        "healthcare": alignment.get("tone_guidelines", "Trustworthy and caring"),
        "real_estate": alignment.get("tone_guidelines", "Premium and elegant"),
        "event": alignment.get("tone_guidelines", "Exciting and clear"),
    }.get(category, "Clear, persuasive, and action-oriented")
    channels = _clean(form_data.get("platform"))
    channel_list = [c.strip() for c in re.split(r"[,/]", channels) if c.strip()] if channels else {
        "food": ["Instagram", "Google Business Profile", "Local community groups", "Delivery apps"],
        "fitness": ["Instagram", "TikTok", "Campus communities", "Student influencers"],
        "education": ["Instagram", "YouTube", "WhatsApp groups", "Parent communities"],
        "beauty": ["Instagram", "TikTok", "Influencer partnerships", "Email"],
        "technology": ["Landing page", "LinkedIn", "Product communities", "Email"],
    }.get(category, ["Social media", "Email", "Website", "Local partnerships"])
    value = {
        "food": "Hot, fresh, affordable meals that make weekend decisions easy",
        "fitness": "Stay fit with quick routines that fit real life",
        "education": "Structured guidance that builds confidence and exam readiness",
        "beauty": "A simple routine for a fresh, confident glow",
        "technology": "A faster, simpler way to get the job done",
        "healthcare": (alignment.get("recommended_benefits") or ["Trusted care for your family"])[0],
        "real_estate": (alignment.get("recommended_benefits") or ["Premium living designed for modern professionals"])[0],
        "event": (alignment.get("recommended_benefits") or ["Live experience with limited seats"])[0],
    }.get(category, f"A practical solution that helps {audience} get better results")
    message = {
        "food": "Hot, fresh favorites at a price that makes weekend ordering easy",
        "fitness": "Fitness that fits your lifestyle",
        "education": "Focused preparation for confident performance",
        "beauty": "Glow with confidence every day",
        "technology": "Simplify your workflow and move faster",
        "healthcare": _clean(form_data.get("offer")) or "FREE HEALTH CHECKUP",
        "real_estate": _clean(form_data.get("offer")) or "EXCLUSIVE SITE VISIT THIS WEEKEND",
        "event": _clean(form_data.get("offer")) or "Reserve your spot today",
    }.get(category, f"{topic} made easier, clearer, and more valuable")
    objective = _infer_objective(topic, text, category)
    result = {
        "campaign_objective": objective,
        "target_audience": audience,
        "audience_pain_points": pains,
        "value_proposition": value,
        "key_marketing_message": message,
        "offer_strategy": offer,
        "recommended_tone": tone,
        "primary_cta": cta,
        "recommended_channels": channel_list,
        "campaign_summary": f"A {audience.lower()} campaign focused on {value.lower()}, using '{message}' to support the {offer} and drive the action: {cta}.",
        "source_prompt": topic,
        "category": category,
        "industry": industry,
    }
    return industry_engine.validate_semantic_alignment(result, alignment)


def format_strategy_for_prompt(strategy: dict[str, Any]) -> str:
    """Format campaign strategy as prompt context for downstream generation."""
    labels = {
        "campaign_objective": "Objective",
        "target_audience": "Audience",
        "audience_pain_points": "Pain Points",
        "value_proposition": "Value Proposition",
        "key_marketing_message": "Marketing Message",
        "offer_strategy": "Offer",
        "recommended_tone": "Tone",
        "primary_cta": "CTA",
        "recommended_channels": "Channels",
        "campaign_summary": "Summary",
    }
    lines = []
    for key in STRATEGY_FIELDS:
        value = strategy.get(key, "")
        if isinstance(value, list):
            value = "; ".join(str(item) for item in value)
        lines.append(f"- {labels[key]}: {value}")
    return "\n".join(lines)


def cta_variations(strategy: dict[str, Any]) -> list[str]:
    primary = _clean(strategy.get("primary_cta"), "Get Started Today")
    offer = _clean(strategy.get("offer_strategy"), "")
    base = [primary, "Start Today", "Get Started Now", "Claim Your Offer", "See What You Can Do"]
    if "trial" in offer.lower():
        base[3] = "Claim Your Free Trial"
    if "demo" in offer.lower():
        base[3] = "Book Your Free Demo"
    if primary == "Order Now":
        base = ["Order Now", "Claim This Weekend Deal", "Get It Fresh Today", "Feed Your Crew", "Tap To Order"]
    return list(dict.fromkeys(base))[:5]


def hashtag_suggestions(strategy: dict[str, Any]) -> list[str]:
    category = _clean(strategy.get("category"), "general")
    tags = {
        "food": ["#PizzaDeal", "#WeekendEats", "#LocalFood", "#OrderNow", "#FamilyDinner", "#Foodie", "#FreshPizza", "#WeekendSpecial", "#Delivery", "#DineLocal", "#HotAndFresh", "#LimitedOffer"],
        "fitness": ["#FitnessApp", "#CollegeFitness", "#FitGoals", "#HealthyHabits", "#QuickWorkouts", "#StudentLife", "#Motivation", "#WorkoutRoutine", "#FitIn15", "#Wellness", "#ActiveLifestyle", "#StartToday"],
        "education": ["#StudentSuccess", "#ExamPrep", "#IITJEE", "#StudySmart", "#Coaching", "#Learning", "#DemoClass", "#AcademicGoals", "#FutureReady", "#ParentCommunity", "#Classroom", "#EnrollNow"],
        "beauty": ["#Skincare", "#GlowUp", "#BeautyRoutine", "#CleanBeauty", "#ShopNow", "#GlowGoals", "#SelfCare", "#PremiumBeauty", "#SkinCareTips", "#BeautyLaunch", "#RadiantSkin", "#LimitedOffer"],
        "technology": ["#ProductLaunch", "#SaaS", "#AppLaunch", "#DigitalTools", "#Productivity", "#TechSolution", "#Startup", "#Workflow", "#Innovation", "#GetStarted", "#TryItNow", "#Growth"],
    }.get(category, ["#Marketing", "#BrandGrowth", "#GetStarted", "#SpecialOffer", "#SmallBusiness", "#Campaign", "#Launch", "#CustomerGrowth", "#Promotion", "#BusinessTips", "#Value", "#CTA"])
    return tags[:15]
