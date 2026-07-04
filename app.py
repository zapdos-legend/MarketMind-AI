"""Flask application entry point for MarketMind-AI.

This module keeps the web layer focused on request handling, validation, and
presentation while delegating prompt construction and AI analysis to the
project's helper modules.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Callable

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

import ai_engine
import campaign_engine
import creative_engine
import design_engine
import prompt_builder


LOGGER = logging.getLogger(__name__)
MAX_INPUT_LENGTH = int(os.environ.get("MAX_ANALYSIS_INPUT_LENGTH", "2000"))
FORM_FIELDS = (
    "content_type",
    "topic",
    "business_name",
    "product_service",
    "audience",
    "platform",
    "tone",
    "offer",
    "notes",
)
REQUIRED_FORM_FIELDS = ("content_type", "topic")
VISUAL_ASSET_TYPES = {"Poster", "Banner", "Pamphlet"}
GENERATED_DIR = Path(__file__).resolve().parent / "generated"


app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key-change-me"),
    ENV=os.environ.get("FLASK_ENV", "production"),
)

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def _first_non_empty_line(text: str) -> str:
    """Return the first meaningful line from generated content."""
    for line in text.splitlines():
        cleaned = line.strip().strip("#*:- ")
        if cleaned:
            return cleaned
    return "Your next campaign starts here"


def _extract_label_value(text: str, labels: tuple[str, ...], default: str) -> str:
    """Extract a simple label-based value from generated marketing content."""
    label_pattern = "|".join(re.escape(label) for label in labels)
    pattern = re.compile(
        rf"^(?:[-*]\s*)?(?:{label_pattern})\s*[:\-]\s*(.+)$",
        re.IGNORECASE,
    )
    for line in text.splitlines():
        match = pattern.match(line.strip())
        if match:
            value = match.group(1).strip().strip("*#")
            if value:
                return value
    return default


def _extract_bullets(text: str, limit: int = 4) -> list[str]:
    """Return concise bullet-like lines from generated content."""
    bullets: list[str] = []
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned.startswith(("- ", "* ", "• ")):
            bullets.append(cleaned[2:].strip())
        if len(bullets) >= limit:
            break
    return bullets or [
        "Benefit-led campaign message",
        "Clear value proposition",
        "Simple next step for customers",
    ]


def _asset_timestamp() -> str:
    """Return a filesystem-friendly UTC timestamp for generated assets."""
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")


def _asset_filename(content_type: str) -> str:
    """Build an asset filename for a supported visual content type."""
    return f"{content_type.lower()}_{_asset_timestamp()}.html"


def _safe_asset_text(value: str, default: str = "") -> str:
    """Normalize short asset text so generated templates stay polished."""
    cleaned = re.sub(r"\s+", " ", str(value or default)).strip()
    return cleaned or default



INTERNAL_STRATEGY_PATTERNS = (
    r"\bpositioned as (?:the )?(?:reason to act now|[^.!,;]+)",
    r"\bemotional trigger\b",
    r"\bcampaign concept\b",
    r"\bcreative angle\b",
    r"\breason to act now\b",
    r"\bdesigned to\b",
    r"\bstrategically framed\b",
    r"\bmarketing message\b",
    r"\boffer framing\b",
    r"\bcreated to drive urgency\b",
)


def _sanitize_asset_copy(value: Any, default: str = "") -> str:
    """Convert strategy-layer wording into customer-facing asset copy."""
    text = _safe_asset_text(str(value or ""), default)
    text = re.sub(r"\s+[—-]\s+positioned as (?:the )?reason to act now\.?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+[—-]\s+(?:created to drive urgency|strategically framed offer|offer framing)\.?", "", text, flags=re.IGNORECASE)
    for pattern in INTERNAL_STRATEGY_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bA clear reason to act now:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bOffer:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bGrab it while it is fresh\.?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bAvailable for a limited time\.?", "LIMITED TIME OFFER", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*[:;,.]\s*$", "", text)
    return _safe_asset_text(text, default)


def _customer_offer_text(value: Any, topic: str = "") -> str:
    """Return a short offer badge that never exposes internal framing."""
    cleaned = _sanitize_asset_copy(value, "")
    combined = f"{cleaned} {topic}".strip()
    match = re.search(r"\b(\d+%\s*off(?:\s+this\s+weekend|\s+weekend)?|free\s+\d+[- ]day\s+trial|\d+[- ]day\s+free\s+trial|free\s+demo\s+class|free\s+demo)\b", combined, re.IGNORECASE)
    if match:
        offer = match.group(1).upper().replace("7-DAY FREE TRIAL", "FREE 7-DAY TRIAL")
        if "50% OFF" in offer and "WEEKEND" in combined.upper() and "WEEKEND" not in offer:
            return "50% OFF THIS WEEKEND"
        return offer
    if "weekend" in combined.lower():
        return "LIMITED WEEKEND DEAL"
    if "trial" in combined.lower():
        return "FREE 7-DAY TRIAL"
    if cleaned:
        return cleaned.upper()[:36]
    return "LIMITED TIME OFFER"


def _customer_benefits(items: list[str], strategy: dict[str, Any], form_data: dict[str, str]) -> list[str]:
    """Sanitize benefit cards and backfill with audience-facing benefits."""
    benefits = [_sanitize_asset_copy(item) for item in items]
    benefits = [item for item in benefits if item and not re.search(r"layout|visual direction|do not generate", item, re.I)]
    text = " ".join(str(form_data.get(k, "")) for k in ("topic", "product_service", "audience", "notes")).lower()
    if "fitness" in text or "workout" in text:
        defaults = ["Quick workouts", "Progress tracking", "Fits busy schedules"]
    elif "pizza" in text or "food" in text:
        defaults = ["Fresh from the oven", "Half-price favorites", "Easy weekend ordering"]
    else:
        defaults = ["Clear value", "Trusted experience", "Simple next step"]
    for item in defaults:
        if len(benefits) >= 3:
            break
        if item not in benefits:
            benefits.append(item)
    return benefits[:3]

def _asset_theme(form_data: dict[str, str], strategy: dict[str, Any] | None = None, creative_strategy: dict[str, Any] | None = None, design_strategy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Choose a professional visual theme from campaign details and strategy."""
    strategy = strategy or {}
    creative_strategy = creative_strategy or {}
    design_strategy = design_strategy or {}
    combined = " ".join(
        [form_data.get(key, "") for key in ("topic", "business_name", "product_service", "audience", "offer", "notes")]
        + [str(strategy.get(key, "")) for key in ("target_audience", "value_proposition", "key_marketing_message", "offer_strategy", "campaign_summary")]
        + [str(creative_strategy.get(key, "")) for key in ("visual_direction", "imagery_direction", "color_mood", "campaign_concept")]
        + [str(design_strategy.get(key, "")) for key in ("design_concept", "layout_type", "background_style", "image_direction", "category")]
    ).lower()
    theme_list = [
        (("fitness", "gym", "workout", "running", "health", "training", "exercise"), "Momentum Fitness", "#111827", "#16a34a", "#f97316", "#dcfce7", "linear-gradient(135deg, #0f172a 0%, #14532d 52%, #f97316 100%)", "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=1200&q=80", ("⚡", "📈", "🏋️"), "Trusted by students building stronger daily routines", "WORKOUT ENERGY"),
        (("cafe", "café", "coffee", "breakfast", "sandwich"), "Morning Café", "#4b2e1f", "#a16207", "#fbbf24", "#fef3c7", "linear-gradient(135deg, #3f2418 0%, #8b5e34 55%, #fbbf24 100%)", "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=1200&q=80", ("☕", "🥪", "🌅"), "Fueling focused mornings for busy office workers", "MORNING COMBO"),
        (("pizza", "restaurant", "food", "meal", "dining", "delivery", "weekend"), "Hot Table", "#7c2d12", "#ef4444", "#facc15", "#ffedd5", "linear-gradient(135deg, #7f1d1d 0%, #ea580c 55%, #facc15 100%)", "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=1200&q=80", ("🍕", "👨‍👩‍👧", "🚚"), "Loved by families, students, and weekend foodies", "HOT & FRESH"),
        (("iit", "jee", "coaching", "academy", "class", "student", "education", "lecture", "learning"), "Scholastic Edge", "#312e81", "#2563eb", "#a855f7", "#e0e7ff", "linear-gradient(135deg, #1e1b4b 0%, #2563eb 56%, #a855f7 100%)", "https://images.unsplash.com/photo-1523580846011-d3a5bc25702b?auto=format&fit=crop&w=1200&q=80", ("🎓", "📚", "💬"), "Trusted by ambitious Class 11 and 12 students", "LEARN SMARTER"),
        (("skin", "skincare", "beauty", "cosmetic", "glow", "premium", "kit"), "Soft Glow", "#831843", "#db2777", "#f9a8d4", "#fce7f3", "linear-gradient(135deg, #831843 0%, #db2777 52%, #f9a8d4 100%)", "https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=1200&q=80", ("✨", "🌿", "💧"), "Loved by Gen Z beauty buyers and glow seekers", "CLEAN GLOW"),
        (("app", "technology", "software", "digital", "ai", "platform", "saas", "dashboard"), "Digital Launch", "#0f172a", "#0284c7", "#22d3ee", "#cffafe", "linear-gradient(135deg, #0f172a 0%, #0369a1 52%, #22d3ee 100%)", "https://images.unsplash.com/photo-1551650975-87deedd944c3?auto=format&fit=crop&w=1200&q=80", ("🚀", "📱", "🔒"), "Built for modern customers who expect fast digital experiences", "DIGITAL READY"),
    ]
    for keywords, name, primary, secondary, accent, soft, gradient, image, icons, proof, visual_label in theme_list:
        if any(keyword in combined for keyword in keywords):
            return {"name": name, "primary": primary, "secondary": secondary, "accent": accent, "soft": soft, "gradient": gradient, "image": image, "icons": icons, "proof": proof, "visual_label": visual_label}
    return {"name": "Agency Classic", "primary": "#3730a3", "secondary": "#4f46e5", "accent": "#06b6d4", "soft": "#eef2ff", "gradient": "linear-gradient(135deg, #312e81 0%, #4f46e5 55%, #06b6d4 100%)", "image": "https://images.unsplash.com/photo-1557804506-669a67965ba0?auto=format&fit=crop&w=1200&q=80", "icons": ("⭐", "📣", "✅"), "proof": "Trusted by customers who want clear value and confident next steps", "visual_label": "CAMPAIGN READY"}


def _theme_image_url(theme: dict[str, Any]) -> str:
    """Return the themed remote image URL used as a CSS background layer."""
    return str(theme["image"])


def _css_fallback_visual(theme: dict[str, Any]) -> str:
    """Return layered CSS that remains attractive if the remote image cannot load."""
    return (
        "linear-gradient(135deg, rgba(255,255,255,.18), rgba(255,255,255,0) 38%),"
        f"{theme['gradient']}"
    )


def _visual_block_html(theme: dict[str, Any], class_name: str = "") -> str:
    """Render a CSS-first visual block with no visible image alt fallback text."""
    classes = f"visual-frame {class_name}".strip()
    return (
        f'<div class="{classes}" style="--asset-image:url(\'{escape(_theme_image_url(theme), quote=True)}\'); '
        f'--fallback-visual:{_css_fallback_visual(theme)};">'
        '<div class="visual-overlay"></div>'
        f'<div class="visual-chip">{escape(str(theme["visual_label"]))}</div>'
        '</div>'
    )


def _icon_card_html(items: list[str], icons: tuple[str, ...]) -> str:
    """Render benefit cards with icons."""
    return "".join(
        f'<article class="benefit-card"><span>{escape(icons[index % len(icons)])}</span><strong>{escape(_safe_asset_text(item))}</strong></article>'
        for index, item in enumerate(items[:3])
    )


def _render_asset_html(content_type: str, result: str, form_data: dict[str, str], strategy: dict[str, Any] | None = None, creative_strategy: dict[str, Any] | None = None, design_strategy: dict[str, Any] | None = None) -> str:
    """Create a standalone HTML asset preview for poster, banner, or pamphlet."""
    topic = _safe_asset_text(form_data.get("topic"), "Marketing Campaign")
    brand = _safe_asset_text(form_data.get("business_name") or form_data.get("product_service"), "MarketMind AI")
    strategy = strategy or {}
    creative_strategy = creative_strategy or {}
    design_strategy = design_strategy or {}
    headline_options = [str(item) for item in creative_strategy.get("headline_options", []) if str(item).strip()] if isinstance(creative_strategy.get("headline_options"), list) else []
    subheadline_options = [str(item) for item in creative_strategy.get("subheadline_options", []) if str(item).strip()] if isinstance(creative_strategy.get("subheadline_options"), list) else []
    cta_options = [str(item) for item in creative_strategy.get("cta_options", []) if str(item).strip()] if isinstance(creative_strategy.get("cta_options"), list) else []
    offer = _customer_offer_text(creative_strategy.get("offer_framing") or strategy.get("offer_strategy") or form_data.get("offer"), topic)
    audience = _sanitize_asset_copy(strategy.get("target_audience") or form_data.get("audience"), "your audience")
    fallback_headline = (
        creative_strategy.get("primary_hook")
        or (headline_options[0] if headline_options else "")
        or _first_non_empty_line(result)
    )
    if content_type == "Pamphlet":
        fallback_headline = creative_strategy.get("campaign_concept") or fallback_headline
    headline = _sanitize_asset_copy(fallback_headline or _extract_label_value(result, ("Headline", "Title"), _first_non_empty_line(result)), "Your next campaign starts here")
    copy_default = (subheadline_options[0] if subheadline_options else creative_strategy.get("creative_angle") or f"A polished campaign preview for {topic}.")
    copy = _sanitize_asset_copy(_extract_label_value(result, ("Supporting copy", "Subheadline", "Introduction", "Subcopy", "Copy", "Body Copy"), copy_default), f"A polished campaign preview for {topic}.")
    cta = _sanitize_asset_copy((cta_options[0] if cta_options else "") or _extract_label_value(result, ("CTA", "Call to action", "Back panel CTA"), str(strategy.get("primary_cta") or "Get started today"))).upper()
    bullets = _customer_benefits([item[2:].strip() if item.lower().startswith(("✓ ", "✔ ")) else item for item in _extract_bullets(result, 3)], strategy, form_data)
    theme = _asset_theme(form_data, strategy, creative_strategy, design_strategy)
    sanitized_result = _sanitize_asset_copy(result, result)
    safe = {key: escape(value) for key, value in {"content_type": content_type, "topic": topic, "brand": brand, "offer": offer, "audience": audience, "headline": headline, "copy": copy, "cta": cta, "result": sanitized_result, "proof": theme["proof"], "theme_name": theme["name"], "layout_type": str(design_strategy.get("layout_type", theme["name"])), "typography": str(design_strategy.get("typography_style", "Bold modern hierarchy"))}.items()}
    benefit_cards = _icon_card_html(bullets, theme["icons"])
    feature_items = "".join(f"<li><span>✓</span>{escape(item)}</li>" for item in bullets)
    visual = _visual_block_html(theme)
    banner_visual = _visual_block_html(theme, "banner-visual")
    if content_type == "Banner":
        asset_body = f"""
        <main class="asset-shell banner-shell"><section class="banner-preview"><div class="banner-content"><p class="eyebrow">{safe['brand']} • {safe['offer']}</p><h1>{safe['headline']}</h1><p class="asset-copy">{safe['copy']}</p><div class="banner-actions"><a class="asset-cta" href="#">{safe['cta']}</a><span class="trust-pill">★ {safe['proof']}</span></div></div>{banner_visual}</section></main>"""
    elif content_type == "Pamphlet":
        asset_body = f"""
        <main class="asset-shell pamphlet-shell"><section class="brochure"><article class="cover panel"><div><p class="eyebrow">{safe['brand']}</p><h1>{safe['headline']}</h1><p>{safe['copy']}</p></div><div class="offer-badge">{safe['offer']}</div>{visual}</article><article class="panel"><p class="section-label">About</p><h2>Built for {safe['audience']}</h2><p>{safe['brand']} brings together clear benefits, practical details, and an easy next step for customers.</p></article><article class="panel"><p class="section-label">Benefits</p><div class="benefit-grid">{benefit_cards}</div></article><article class="panel"><p class="section-label">Features</p><ul class="feature-list">{feature_items}<li><span>✓</span>Simple contact path and conversion-ready messaging</li></ul></article><article class="panel proof-panel"><p class="section-label">Why choose us</p><h2>{safe['proof']}</h2><p>Consistent visuals, audience-first copy, and practical proof help customers feel confident from the first glance.</p></article><article class="panel offer-panel"><p class="section-label">Special offer</p><h2>{safe['offer']}</h2><a class="asset-cta" href="#">{safe['cta']}</a><div class="qr-box">QR<br>CODE</div><p class="contact-line">Contact: hello@example.com • www.example.com • Your City</p></article></section></main>"""
    else:
        asset_body = f"""
        <main class="asset-shell poster-shell"><section class="poster-preview"><div class="brand-row"><div class="logo-mark">{escape(brand[:1].upper())}</div><div><strong>{safe['brand']}</strong><small>{safe['layout_type']}</small></div></div><div class="poster-hero"><div class="poster-copy"><p class="eyebrow">For {safe['audience']}</p><h1>{safe['headline']}</h1><p class="asset-copy">{safe['copy']}</p><div class="benefit-grid">{benefit_cards}</div><a class="asset-cta" href="#">{safe['cta']}</a></div><div class="visual-wrap"><div class="offer-badge">{safe['offer']}</div>{visual}</div></div><div class="poster-footer"><span>★ {safe['proof']}</span><span>hello@example.com • www.example.com</span></div></section></main>"""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{safe['content_type']} Preview | {safe['brand']}</title><style>
:root {{ color-scheme:light; --ink:#0f172a; --muted:#64748b; --primary:{theme['primary']}; --secondary:{theme['secondary']}; --accent:{theme['accent']}; --soft:{theme['soft']}; --gradient:{theme['gradient']}; }} *{{box-sizing:border-box}} body{{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:radial-gradient(circle at 12% 10%,var(--soft),transparent 24rem),#f8fafc}} .asset-shell{{min-height:100vh;display:grid;place-items:center;padding:clamp(1rem,4vw,4rem)}} .poster-preview,.banner-preview,.brochure{{width:min(100%,76rem);border-radius:2.25rem;overflow:hidden;box-shadow:0 2.5rem 6rem rgba(15,23,42,.24)}} .poster-preview{{min-height:82vh;padding:clamp(1.35rem,4vw,3.5rem);background:linear-gradient(135deg,rgba(255,255,255,.95),rgba(255,255,255,.78)),var(--gradient)}} .brand-row,.poster-footer,.banner-actions{{display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap}} .logo-mark{{width:3.25rem;height:3.25rem;border-radius:1rem;display:grid;place-items:center;background:var(--gradient);color:white;font-weight:950;font-size:1.5rem}} .brand-row small{{display:block;color:var(--muted);font-weight:700;margin-top:.15rem}} .poster-hero{{display:grid;grid-template-columns:1.05fr .95fr;gap:clamp(1.5rem,4vw,4rem);align-items:center;padding:clamp(2rem,6vw,5rem) 0}} .eyebrow,.section-label{{margin:0 0 1rem;text-transform:uppercase;letter-spacing:.15em;font-weight:900;color:var(--secondary);font-size:.8rem}} h1{{margin:0;font-size:clamp(3rem,8vw,7rem);line-height:.88;letter-spacing:-.07em;max-width:9.5ch}} h2{{margin:.1rem 0 1rem;font-size:clamp(1.6rem,3vw,2.3rem);line-height:1.02;letter-spacing:-.04em}} .asset-copy,p,li{{font-size:clamp(1rem,1.8vw,1.25rem);line-height:1.55}} .asset-copy{{color:#334155;max-width:42rem}} .visual-wrap,.visual-frame{{position:relative}} .visual-frame{{min-height:25rem;border-radius:2rem;overflow:hidden;background-image:linear-gradient(135deg,rgba(15,23,42,.12),rgba(15,23,42,.54)),var(--asset-image),var(--fallback-visual);background-size:cover;background-position:center;box-shadow:inset 0 0 0 1px rgba(255,255,255,.22),0 1.5rem 3rem rgba(15,23,42,.2);isolation:isolate}} .visual-overlay{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(255,255,255,.08),rgba(15,23,42,.38));z-index:1}} .visual-chip{{position:absolute;left:1.1rem;bottom:1.1rem;z-index:2;padding:.7rem .9rem;border-radius:999px;background:rgba(255,255,255,.88);color:var(--primary);font-weight:950;letter-spacing:.08em;font-size:.76rem;box-shadow:0 .75rem 1.5rem rgba(15,23,42,.18)}} .offer-badge{{position:absolute;z-index:4;top:1rem;right:1rem;max-width:14rem;padding:1rem 1.15rem;border-radius:999px;background:var(--accent);color:#111827;font-weight:950;text-transform:uppercase;letter-spacing:.05em;text-align:center;box-shadow:0 1rem 2rem rgba(15,23,42,.22)}} .benefit-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin:2rem 0}} .benefit-card{{padding:1.15rem;border-radius:1.25rem;background:rgba(255,255,255,.82);border:1px solid rgba(15,23,42,.08);box-shadow:0 .8rem 1.8rem rgba(15,23,42,.08)}} .benefit-card span{{display:block;font-size:1.65rem;margin-bottom:.6rem}} .asset-cta{{display:inline-flex;align-items:center;justify-content:center;padding:1rem 1.4rem;border-radius:999px;background:var(--ink);color:white;text-decoration:none;font-weight:950;box-shadow:0 1rem 2rem rgba(15,23,42,.2)}} .poster-footer{{border-top:1px solid rgba(15,23,42,.1);padding-top:1.25rem;color:#334155;font-weight:800}} .banner-preview{{min-height:22rem;padding:clamp(1.5rem,5vw,4rem);display:grid;grid-template-columns:1.2fr .8fr;gap:2rem;align-items:center;background:var(--gradient);color:white}} .banner-preview h1{{font-size:clamp(2.4rem,5.4vw,5.5rem);max-width:11ch}} .banner-preview .eyebrow,.banner-preview .asset-copy{{color:white}} .banner-preview .asset-copy{{opacity:.9}} .banner-visual{{min-height:18rem;border:8px solid rgba(255,255,255,.24);transform:rotate(2deg)}} .banner-preview .asset-cta{{background:white;color:var(--primary)}} .trust-pill{{padding:.85rem 1rem;border-radius:999px;background:rgba(255,255,255,.16);font-weight:800}} .brochure{{display:grid;grid-template-columns:repeat(3,1fr);background:#fff}} .panel{{min-height:25rem;padding:clamp(1.25rem,3vw,2rem);border:1px solid rgba(15,23,42,.08);position:relative;overflow:hidden}} .cover{{grid-row:span 2;display:flex;flex-direction:column;justify-content:space-between;background:var(--gradient);color:white}} .cover .eyebrow,.cover p{{color:white}} .cover .visual-frame{{min-height:14rem;margin-top:1.25rem}} .cover .offer-badge{{position:static;display:inline-block;margin:1rem 0}} .feature-list{{list-style:none;padding:0;margin:0}} .feature-list li{{display:flex;gap:.65rem;margin-bottom:.8rem}} .feature-list span{{color:var(--secondary);font-weight:950}} .proof-panel{{background:var(--soft)}} .offer-panel{{background:#0f172a;color:white;display:flex;flex-direction:column;justify-content:center}} .offer-panel .section-label,.offer-panel p{{color:white}} .offer-panel .asset-cta{{background:white;color:#0f172a}} .qr-box{{width:7rem;height:7rem;margin:1.4rem 0;border-radius:1rem;display:grid;place-items:center;text-align:center;background:repeating-linear-gradient(45deg,#fff 0 8px,#e2e8f0 8px 16px);color:#0f172a;font-weight:950}} .contact-line{{font-size:.95rem;opacity:.86}} .source-copy{{padding:2rem;max-width:76rem;margin:0 auto 3rem;background:rgba(255,255,255,.82);border-radius:1.25rem;white-space:pre-wrap}} .source-copy pre{{white-space:pre-wrap;overflow-wrap:anywhere}} @media (max-width:920px){{.poster-hero,.banner-preview,.brochure{{grid-template-columns:1fr}}.benefit-grid{{grid-template-columns:1fr}}.visual-frame{{min-height:18rem}}.panel{{min-height:auto}}h1{{max-width:12ch}}}} @media (max-width:560px){{.asset-shell{{padding:.75rem}}.poster-preview,.banner-preview,.brochure{{border-radius:1.35rem}}h1{{font-size:clamp(2.45rem,16vw,4rem)}}.banner-actions{{align-items:stretch}}.asset-cta,.trust-pill{{width:100%}}}}
</style></head><body>{asset_body}</body></html>"""

def _create_visual_asset(result: str, form_data: dict[str, str], strategy: dict[str, Any] | None = None, creative_strategy: dict[str, Any] | None = None, design_strategy: dict[str, Any] | None = None) -> dict[str, str] | None:
    """Create a downloadable HTML preview for supported visual assets."""
    content_type = form_data.get("content_type", "")
    if content_type not in VISUAL_ASSET_TYPES:
        return None

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    filename = _asset_filename(content_type)
    (GENERATED_DIR / filename).write_text(
        _render_asset_html(content_type, result, form_data, strategy, creative_strategy, design_strategy),
        encoding="utf-8",
    )
    return {"filename": filename, "label": f"{content_type} preview"}


def _get_callable(module: Any, names: tuple[str, ...]) -> Callable[..., Any] | None:
    """Return the first callable attribute found in *module* from *names*."""
    for name in names:
        candidate = getattr(module, name, None)
        if callable(candidate):
            return candidate
    return None


def _clean_form_value(field_name: str) -> str:
    """Normalize a submitted form value into a safe, trimmed string."""
    return request.form.get(field_name, "").strip()


def _validate_analysis_request() -> tuple[dict[str, str], list[str]]:
    """Validate the analysis form and return sanitized data plus errors."""
    cleaned_data = {field_name: _clean_form_value(field_name) for field_name in FORM_FIELDS}
    errors: list[str] = []

    for field_name in REQUIRED_FORM_FIELDS:
        if not _clean_form_value(field_name):
            errors.append(f"Please provide a {field_name.replace('_', ' ')}.")

    for field_name, value in cleaned_data.items():
        if len(value) > MAX_INPUT_LENGTH:
            errors.append(
                f"{field_name.replace('_', ' ').title()} must be "
                f"{MAX_INPUT_LENGTH} characters or fewer."
            )

    return cleaned_data, errors


def _build_prompt(form_data: dict[str, str], strategy: dict[str, Any] | None = None, creative_strategy: dict[str, Any] | None = None, design_strategy: dict[str, Any] | None = None) -> Any:
    """Build an AI prompt using prompt_builder.py's public helper."""
    builder = _get_callable(
        prompt_builder,
        ("build_prompt", "create_prompt", "generate_prompt", "build_analysis_prompt"),
    )
    if builder is None:
        raise RuntimeError("prompt_builder.py does not expose a prompt builder function.")

    try:
        return builder(form_data, strategy, creative_strategy, design_strategy)
    except TypeError:
        try:
            return builder(form_data, strategy)
        except TypeError:
            data = dict(form_data)
            data["campaign_strategy"] = strategy
            data["creative_strategy"] = creative_strategy
            data["design_strategy"] = design_strategy
            return builder(data)


def _run_analysis(prompt: Any) -> Any:
    """Run the prompt through ai_engine.py's public analysis helper."""
    analyzer = _get_callable(
        ai_engine,
        ("analyze", "run_analysis", "analyze_market", "get_ai_response"),
    )
    if analyzer is None:
        raise RuntimeError("ai_engine.py does not expose an analysis function.")

    return analyzer(prompt)


@app.route("/", methods=["GET"])
def index() -> str:
    """Render the landing page with the market-analysis form."""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze() -> str:
    """Validate user input, run analysis, and render the result page."""
    form_data, validation_errors = _validate_analysis_request()
    if validation_errors:
        for error in validation_errors:
            flash(error, "error")
        return redirect(url_for("index"))

    try:
        campaign_strategy = campaign_engine.build_campaign_strategy(form_data)
        creative_strategy = creative_engine.build_creative_strategy(form_data, campaign_strategy)
        design_strategy = design_engine.build_design_strategy(form_data, campaign_strategy, creative_strategy)
        prompt = _build_prompt(form_data, campaign_strategy, creative_strategy, design_strategy)
        result = _run_analysis(prompt)
        asset = _create_visual_asset(str(result), form_data, campaign_strategy, creative_strategy, design_strategy)
    except RuntimeError as exc:
        LOGGER.warning("Application configuration error: %s", exc)
        flash(str(exc), "error")
        return redirect(url_for("index"))
    except Exception:
        LOGGER.exception("Unexpected error while analyzing request")
        flash("We could not complete the analysis. Please try again.", "error")
        return redirect(url_for("index"))

    flash("Analysis completed successfully.", "success")
    return render_template("result.html", result=result, form_data=form_data, asset=asset, campaign_strategy=campaign_strategy, creative_strategy=creative_strategy, design_strategy=design_strategy)


@app.route("/generated/<path:filename>", methods=["GET"])
def open_generated_asset(filename: str):
    """Serve a generated visual asset preview in the browser."""
    return send_from_directory(GENERATED_DIR, filename, mimetype="text/html")


@app.route("/generated/<path:filename>/download", methods=["GET"])
def download_generated_asset(filename: str):
    """Download a generated visual asset preview file."""
    return send_from_directory(GENERATED_DIR, filename, as_attachment=True)


@app.errorhandler(404)
def not_found(error: Exception) -> tuple[str, int]:
    """Handle unknown routes with a friendly flash message."""
    LOGGER.info("404 error: %s", error)
    flash("The requested page could not be found.", "error")
    return render_template("index.html"), 404


@app.errorhandler(500)
def internal_error(error: Exception) -> tuple[str, int]:
    """Handle server errors without exposing implementation details."""
    LOGGER.exception("Unhandled server error: %s", error)
    flash("An unexpected server error occurred. Please try again later.", "error")
    return render_template("index.html"), 500


if __name__ == "__main__":
    app.run(
        host=os.environ.get("FLASK_RUN_HOST", "127.0.0.1"),
        port=int(os.environ.get("FLASK_RUN_PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
    )
