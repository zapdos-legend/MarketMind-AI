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

import campaign_engine


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



def _extract_strategy_detail(prompt: str, label: str) -> str:
    """Return a campaign strategy detail from the prompt, if present."""
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

    strategy_audience = _extract_strategy_detail(prompt, "Audience")
    strategy_offer = _extract_strategy_detail(prompt, "Offer")
    strategy_tone = _extract_strategy_detail(prompt, "Tone")
    strategy_cta = _extract_strategy_detail(prompt, "CTA")
    strategy_message = _extract_strategy_detail(prompt, "Marketing Message")
    strategy_value = _extract_strategy_detail(prompt, "Value Proposition")
    strategy_pains = _extract_strategy_detail(prompt, "Pain Points")
    primary_hook = _extract_strategy_detail(prompt, "Primary Hook")
    headline_options = _extract_strategy_detail(prompt, "Headline Options")
    subheadline_options = _extract_strategy_detail(prompt, "Subheadline Options")
    offer_framing = _extract_strategy_detail(prompt, "Offer Framing")
    cta_options = _extract_strategy_detail(prompt, "CTA Options")
    visual_direction = _extract_strategy_detail(prompt, "Visual Direction")
    imagery_direction = _extract_strategy_detail(prompt, "Imagery Direction")
    campaign_concept = _extract_strategy_detail(prompt, "Campaign Concept")
    creative_angle = _extract_strategy_detail(prompt, "Creative Angle")
    brand = business_name or product_service or "MarketMind AI"

    return {
        "topic": topic,
        "brand": brand,
        "product_service": product_service,
        "audience": strategy_audience or audience,
        "platform": platform,
        "tone": strategy_tone or tone,
        "offer": strategy_offer or offer,
        "strategy_cta": strategy_cta,
        "strategy_message": strategy_message,
        "strategy_value": strategy_value,
        "strategy_pains": strategy_pains,
        "primary_hook": primary_hook,
        "headline_options": headline_options,
        "subheadline_options": subheadline_options,
        "offer_framing": offer_framing,
        "cta_options": cta_options,
        "visual_direction": visual_direction,
        "imagery_direction": imagery_direction,
        "campaign_concept": campaign_concept,
        "creative_angle": creative_angle,
    }


def _title_case_phrase(text: str) -> str:
    """Return compact title case without preserving noisy prompt verbs."""
    cleaned = re.sub(r"\b(promote|launch|create|advertise|announce)\b", "", text, flags=re.IGNORECASE)
    cleaned = " ".join(cleaned.replace("/", " / ").split())
    return cleaned.title() if cleaned else text.title()


def _is_offer(topic: str, offer: str = "") -> bool:
    """Detect whether the request contains a promotional offer."""
    combined = f"{topic} {offer}".lower()
    return bool(re.search(r"\b(\d+%|off|sale|deal|discount|free|trial|weekend|limited|demo)\b", combined))


def _detect_category(topic: str, audience: str = "") -> str:
    """Map a request to a broad category for stronger fallback copy."""
    combined = f"{topic} {audience}".lower()
    if any(word in combined for word in ("fitness", "workout", "gym", "health")):
        return "fitness"
    if any(word in combined for word in ("pizza", "restaurant", "food", "meal")):
        return "food"
    if any(word in combined for word in ("iit", "jee", "coaching", "academy", "class", "student")):
        return "education"
    if any(word in combined for word in ("skin", "beauty", "skincare", "glow")):
        return "beauty"
    return "general"


def _audience_phrase(audience: str) -> str:
    return f" for {audience}" if audience else ""


def _split_prompt_list(value: str) -> list[str]:
    """Split semicolon-delimited prompt context into clean options."""
    return [item.strip() for item in value.split(";") if item.strip()]


def generate_headline(topic: str, brand: str = "", audience: str = "", offer: str = "") -> str:
    """Generate a benefit-first headline that avoids prompt-rewriter phrasing."""
    category = _detect_category(topic, audience)
    offer_source = offer or topic
    offer_match = re.search(r"(\d+%\s*off[^,.!]*|free\s+[\w -]+|free\s+demo\s+lecture)", offer_source, re.IGNORECASE)
    if offer_match:
        return offer_match.group(1).strip().upper()
    if category == "fitness":
        return "GET FIT. STAY FOCUSED."
    if category == "food" and _is_offer(topic, offer):
        return "50% OFF PIZZA THIS WEEKEND" if "50" in f"{topic} {offer}" else "FRESH DEALS. HOT FLAVOR."
    if category == "education":
        return "BUILD YOUR IIT/JEE EDGE"
    if category == "beauty":
        return "GLOW STARTS HERE"
    return f"{_title_case_phrase(topic)} That Gets Results"


def generate_subheadline(topic: str, brand: str = "", audience: str = "", offer: str = "") -> str:
    """Generate concise supporting copy with value and audience fit."""
    category = _detect_category(topic, audience)
    audience_text = _audience_phrase(audience)
    if category == "fitness":
        return f"The fitness app designed for busy {audience or 'people who want better routines'}."
    if category == "food":
        return "Your favorite pizzas at half price, fresh from the oven all weekend."
    if category == "education":
        return f"Focused coaching, expert guidance, and exam-ready practice{audience_text}."
    if category == "beauty":
        return f"A premium skincare ritual made for fresh, confident glow{audience_text}."
    if offer:
        return f"A clear reason to act now: {offer}."
    return f"A practical, benefit-led solution{audience_text} from {brand or 'your brand'}."


def generate_benefits(topic: str, audience: str = "", limit: int = 3) -> list[str]:
    """Return audience-relevant benefit bullets."""
    category = _detect_category(topic, audience)
    benefits_by_category = {
        "fitness": ["Quick Workouts", "Goal Tracking", "Personalized Plans"],
        "food": ["Half-Price Favorites", "Family-Friendly Combos", "Hot Weekend Delivery"],
        "education": ["Expert Faculty", "Exam-Focused Practice", "Personal Doubt Support"],
        "beauty": ["Visible Glow", "Premium Ingredients", "Easy Daily Routine"],
        "general": ["Clear Value", "Fast Results", "Simple Next Step"],
    }
    return benefits_by_category[category][:limit]


def generate_cta(topic: str, offer: str = "", content_type: str = "") -> str:
    """Generate an action-oriented CTA from the offer and content type."""
    combined = f"{topic} {offer}".lower()
    if "trial" in combined:
        return "Start Your Free Trial"
    if "demo" in combined:
        return "Book Your Free Demo"
    if any(word in combined for word in ("pizza", "food", "meal")):
        return "Order Now"
    if any(word in combined for word in ("shop", "skincare", "beauty", "kit")):
        return "Shop Now"
    if content_type == "Article":
        return "Explore the offer today"
    return "Get Started Today"


def generate_offer_copy(topic: str, offer: str = "") -> str:
    """Generate urgency and offer copy without inventing when no offer exists."""
    if offer:
        return f"Offer: {offer}. Grab it while it is fresh."
    if _is_offer(topic):
        return f"Offer: {_title_case_phrase(topic)}. Available for a limited time."
    return "Offer: Ask about current packages, pricing, and launch specials."


def _visual_guidance(content_type: str) -> str:
    """Return visual/layout guidance for copy-only visual formats."""
    if content_type == "Poster":
        return "Use a bold brand lockup, oversized headline, three benefit ticks, and a high-contrast CTA block."
    if content_type == "Banner":
        return "Use a short headline, one support line, and a button-style CTA with generous whitespace."
    return "Organize the pamphlet into clear panels: cover, introduction, benefits, features, offer, CTA, and contact."


def _local_fallback(prompt: str, reason: str | None = None) -> str:
    """Build deterministic marketing content without weak prompt-rewriter copy."""
    content_type = _extract_content_type(prompt)
    context = _fallback_context(prompt)
    brand = context["brand"]
    topic = context["topic"]
    audience = context["audience"]
    offer = context["offer"]
    platform = context["platform"]
    tone = context["tone"]
    strategy_cta = context.get("strategy_cta", "")
    strategy_message = context.get("strategy_message", "")
    strategy_value = context.get("strategy_value", "")
    strategy_pains = context.get("strategy_pains", "")
    primary_hook = context.get("primary_hook", "")
    headline_options = _split_prompt_list(context.get("headline_options", ""))
    subheadline_options = _split_prompt_list(context.get("subheadline_options", ""))
    cta_options = _split_prompt_list(context.get("cta_options", ""))
    offer_framing = context.get("offer_framing", "")
    visual_direction = context.get("visual_direction", "")
    imagery_direction = context.get("imagery_direction", "")
    campaign_concept = context.get("campaign_concept", "")
    creative_angle = context.get("creative_angle", "")
    headline = primary_hook or (headline_options[0] if headline_options else "") or (strategy_message.upper() if strategy_message else generate_headline(topic, brand, audience, offer))
    if content_type == "Poster" and primary_hook:
        headline = primary_hook
    subheadline = (subheadline_options[0] if subheadline_options else "") or strategy_value or generate_subheadline(topic, brand, audience, offer)
    cta = (cta_options[0] if cta_options else "") or strategy_cta or generate_cta(topic, offer, content_type)
    benefits = generate_benefits(topic, audience)
    offer_copy = offer_framing or generate_offer_copy(topic, offer)
    note = f"\n\nNote: Using local fallback because {reason}." if reason else ""
    tone_line = f"\nTone: {tone}" if tone else ""
    platform_line = f"\nPlatform: {platform}" if platform else ""

    if content_type == "Article":
        return f"""# {headline.title()}

## Introduction
{brand} helps {audience or 'customers'} move from interest to action with a clear value proposition: {subheadline}

## 1. Why This Matters
People respond when the promise is specific, relevant, and easy to act on. {brand} leads with outcomes instead of generic claims.

## 2. What Customers Get
- {benefits[0]}
- {benefits[1]}
- {benefits[2]}

## 3. The Offer
{offer_copy}

## 4. How To Take The Next Step
Choose the option that fits your goal, then follow the CTA while motivation is high.

## Conclusion
Strong marketing gives people a reason to care and a simple path to respond.

CTA: {cta}.{note}"""

    if content_type == "Social Media Caption":
        hashtags = _hashtags(brand, topic, audience)
        return f"""Hook: {headline}

Body: {subheadline} {offer_copy}

CTA: {cta}.

Hashtags: {hashtags}{tone_line}{platform_line}{note}"""

    if content_type == "Poster":
        return f"""Poster Copy
Brand: {brand.upper()}
Headline: {headline}
Subheadline: {subheadline}
Benefits:
- ✓ {benefits[0]}
- ✓ {benefits[1]}
- ✓ {benefits[2]}
CTA: {cta}
Offer: {offer_copy}

Layout / Visual Direction
{(visual_direction + " " + imagery_direction).strip() or _visual_guidance(content_type)} Do not generate an actual image.{note}"""

    if content_type == "Banner":
        return f"""Banner Copy
Headline: {headline}
Supporting copy: {subheadline}
CTA: {cta}

Layout / Visual Direction
{(visual_direction + " " + imagery_direction).strip() or _visual_guidance(content_type)} Do not generate an actual image.{note}"""

    if content_type == "Pamphlet":
        return f"""Pamphlet Copy
Headline: {campaign_concept or headline}
Introduction: {creative_angle or subheadline}

Benefits:
- {benefits[0]}
- {benefits[1]}
- {benefits[2]}

Features:
- Structured guidance tailored to {audience or 'your audience'}
- Clear next steps from first interest to conversion
- Practical details that build trust quickly

Offer:
{offer_copy}

CTA: {cta}

Contact Section:
Contact {brand} today to learn more, ask questions, and reserve your spot.

Layout / Visual Direction
{(visual_direction + " " + imagery_direction).strip() or _visual_guidance(content_type)} Do not generate an actual image.{note}"""

    if content_type == "AI Marketing Pack":
        strategy = {"primary_cta": cta, "offer_strategy": offer, "category": _detect_category(topic, audience)}
        ctas = "\n".join(f"- {item}" for item in (cta_options or campaign_engine.cta_variations(strategy)))
        hashtags = " ".join(campaign_engine.hashtag_suggestions(strategy))
        return f"""Campaign Strategy
Objective: {_extract_strategy_detail(prompt, "Objective") or "Drive measurable campaign action"}
Audience: {audience}
Pain Points: {strategy_pains or "; ".join(generate_benefits(topic, audience))}
Value Proposition: {subheadline}
Marketing Message: {strategy_message or headline}
Offer: {offer_copy}
CTA: {cta}

Creative Strategy
Campaign Concept: {campaign_concept or headline}
Creative Angle: {creative_angle or subheadline}
Primary Hook: {primary_hook or headline}
Headline Options: {"; ".join(headline_options) or headline}
Visual Direction: {visual_direction or _visual_guidance("Poster")}
CTA Options: {"; ".join(cta_options) or cta}

Marketing Copy
Headline: {headline}
Body Copy: {subheadline} {offer_copy}
CTA: {cta}

Poster
Brand: {brand.upper()}
Headline: {primary_hook or headline}
Subheadline: {subheadline}
Benefits: {', '.join(benefits)}
CTA: {cta}

Banner
Headline: {(min(headline_options, key=len) if headline_options else headline)}
Supporting copy: {subheadline}
CTA: {cta}

Pamphlet
Title: {campaign_concept or headline}
Introduction: {creative_angle or subheadline}
Benefits: {', '.join(benefits)}
Offer: {offer_copy}
CTA: {cta}

Social Caption
Hook: {headline}
Body: {subheadline} {offer_copy}
CTA: {cta}.

CTA Variations
{ctas}

Hashtag Suggestions
{hashtags}{note}"""

    return f"""Headline
{headline}

Body Copy
{subheadline} {offer_copy} Built to help {audience or 'customers'} understand the value quickly and take action with confidence.

CTA
{cta}.{note}"""


def _hashtags(brand: str, topic: str, audience: str = "") -> str:
    """Create relevant lightweight hashtags for fallback content."""
    category = _detect_category(topic, audience)
    tags = {
        "fitness": ["#FitnessApp", "#CollegeFitness", "#FitGoals", "#HealthyHabits"],
        "food": ["#PizzaDeal", "#WeekendOffer", "#FamilyPizza", "#OrderNow"],
        "education": ["#IITJEE", "#ExamPrep", "#CoachingClasses", "#StudentSuccess"],
        "beauty": ["#Skincare", "#GlowUp", "#BeautyRoutine", "#GenZBeauty"],
        "general": ["#Marketing", "#BrandGrowth", "#GetStarted", "#SpecialOffer"],
    }[category]
    brand_tag = "#" + re.sub(r"[^A-Za-z0-9]", "", brand.title()) if brand else "#MarketMindAI"
    return " ".join([brand_tag, *tags])


def _call_openai(prompt: str, api_key: str) -> str:
    """Call OpenAI's Responses API and return the generated text."""
    payload = {
        "model": os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
        "input": prompt,
        "instructions": (
            "You are a senior marketing copywriter. Write finished marketing copy, "
            "not prompt rewrites or generic strategy. Follow the requested content "
            "type and sections exactly. Lead with concrete benefits, audience fit, "
            "emotional hooks, urgency when relevant, and action-oriented CTAs. Never "
            "use weak filler such as 'Make X easier', 'value customers can say yes to', 'unlock your potential', 'take your business to the next level', 'act now while it is available', or 'designed for success'. For poster, banner, and pamphlet "
            "requests, provide copy plus layout or visual guidance only."
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
