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


def _render_asset_html(content_type: str, result: str, form_data: dict[str, str]) -> str:
    """Create a standalone HTML asset preview for poster, banner, or pamphlet."""
    topic = form_data.get("topic") or "Marketing Campaign"
    brand = form_data.get("business_name") or form_data.get("product_service") or "MarketMind AI"
    offer = form_data.get("offer") or "Limited-time offer"
    audience = form_data.get("audience") or "your audience"
    headline = _extract_label_value(result, ("Headline", "Title"), _first_non_empty_line(result))
    copy = _extract_label_value(
        result,
        ("Supporting copy", "Subheadline", "Introduction", "Subcopy", "Copy", "Body Copy"),
        f"A polished campaign preview for {topic}.",
    )
    cta = _extract_label_value(
        result,
        ("CTA", "Call to action", "Back panel CTA"),
        "Get started today",
    )
    bullets = _extract_bullets(result)
    if any(item.lower().startswith(("✓ ", "✔ ")) for item in bullets):
        bullets = [item[2:].strip() if item.lower().startswith(("✓ ", "✔ ")) else item for item in bullets]

    safe = {
        "content_type": escape(content_type),
        "topic": escape(topic),
        "brand": escape(brand),
        "offer": escape(offer),
        "audience": escape(audience),
        "headline": escape(headline),
        "copy": escape(copy),
        "cta": escape(cta),
        "result": escape(result),
    }
    bullet_items = "".join(f"<li>{escape(item)}</li>" for item in bullets)

    if content_type == "Banner":
        asset_body = f"""
        <main class="asset-shell banner-shell">
            <section class="banner-preview">
                <div>
                    <p class="eyebrow">{safe['brand']} • {safe['offer']}</p>
                    <h1>{safe['headline']}</h1>
                    <p class="asset-copy">{safe['copy']}</p>
                </div>
                <a class="asset-cta" href="#details">{safe['cta']}</a>
            </section>
        </main>"""
    elif content_type == "Pamphlet":
        asset_body = f"""
        <main class="asset-shell pamphlet-shell">
            <section class="pamphlet-grid">
                <article class="pamphlet-panel hero-panel">
                    <p class="eyebrow">{safe['brand']}</p>
                    <h1>{safe['headline']}</h1>
                    <p>{safe['copy']}</p>
                </article>
                <article class="pamphlet-panel"><h2>Features</h2><ul>{bullet_items}</ul></article>
                <article class="pamphlet-panel"><h2>Benefits</h2><p>Designed for {safe['audience']} with clear messaging, strong positioning, and fast campaign adaptation.</p></article>
                <article class="pamphlet-panel"><h2>Offer</h2><p>{safe['offer']}</p></article>
                <article class="pamphlet-panel cta-panel"><h2>Ready to act?</h2><a class="asset-cta" href="#details">{safe['cta']}</a></article>
            </section>
        </main>"""
    else:
        asset_body = f"""
        <main class="asset-shell poster-shell">
            <section class="poster-preview">
                <p class="eyebrow">{safe['brand']}</p>
                <h1>{safe['headline']}</h1>
                <p class="asset-copy">{safe['copy']}</p>
                <div class="poster-offer">{safe['offer']}</div>
                <a class="asset-cta" href="#details">{safe['cta']}</a>
            </section>
        </main>"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{safe['content_type']} Preview | {safe['brand']}</title>
<style>
:root {{ color-scheme: light; --ink:#0f172a; --muted:#64748b; --primary:#4f46e5; --accent:#06b6d4; --paper:#ffffff; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: linear-gradient(135deg, #eef2ff, #ecfeff 55%, #fff7ed); }}
.asset-shell {{ min-height: 100vh; display: grid; place-items: center; padding: clamp(1.25rem, 4vw, 4rem); }}
.poster-preview, .banner-preview, .pamphlet-panel {{ border: 1px solid rgba(15,23,42,.1); box-shadow: 0 2rem 5rem rgba(15,23,42,.18); background: rgba(255,255,255,.92); }}
.poster-preview {{ width: min(100%, 46rem); min-height: 75vh; border-radius: 2rem; padding: clamp(2rem, 7vw, 5rem); display: flex; flex-direction: column; justify-content: center; text-align: center; background: radial-gradient(circle at top right, rgba(6,182,212,.28), transparent 18rem), linear-gradient(160deg, #fff, #eef2ff); }}
.banner-preview {{ width: min(100%, 72rem); min-height: 19rem; border-radius: 2rem; padding: clamp(1.5rem, 5vw, 4rem); display: flex; align-items: center; justify-content: space-between; gap: 2rem; background: linear-gradient(135deg, #111827, #3730a3 55%, #06b6d4); color: white; }}
.pamphlet-grid {{ width: min(100%, 76rem); display: grid; grid-template-columns: repeat(5, minmax(12rem, 1fr)); gap: 1rem; }}
.pamphlet-panel {{ min-height: 28rem; border-radius: 1.5rem; padding: 1.5rem; display: flex; flex-direction: column; justify-content: center; }}
.hero-panel, .cta-panel {{ background: linear-gradient(160deg, #4f46e5, #06b6d4); color: white; }}
.eyebrow {{ margin: 0 0 1rem; text-transform: uppercase; letter-spacing: .14em; font-weight: 800; color: inherit; opacity: .82; }}
h1 {{ margin: 0; font-size: clamp(2.5rem, 8vw, 6rem); line-height: .92; letter-spacing: -.06em; }}
.banner-preview h1 {{ font-size: clamp(2rem, 5vw, 4.6rem); max-width: 13ch; }}
h2 {{ margin: 0 0 1rem; font-size: 1.4rem; }}
.asset-copy, .poster-preview p:not(.eyebrow), .pamphlet-panel p, li {{ font-size: clamp(1rem, 2vw, 1.35rem); line-height: 1.55; color: inherit; }}
.poster-offer {{ margin: 2rem auto 1rem; padding: .85rem 1.25rem; border-radius: 999px; background: #f97316; color: white; font-weight: 900; }}
.asset-cta {{ display: inline-flex; align-items: center; justify-content: center; margin-top: 1.25rem; padding: 1rem 1.5rem; border-radius: 999px; background: #0f172a; color: white; text-decoration: none; font-weight: 900; box-shadow: 0 1rem 2rem rgba(15,23,42,.18); }}
.banner-preview .asset-cta, .cta-panel .asset-cta {{ background: white; color: #3730a3; white-space: nowrap; }}
ul {{ padding-left: 1.25rem; }}
.source-copy {{ padding: 2rem; max-width: 72rem; margin: 0 auto 3rem; background: rgba(255,255,255,.75); border-radius: 1.25rem; white-space: pre-wrap; }}
.source-copy pre {{ white-space: pre-wrap; overflow-wrap: anywhere; }}
@media (max-width: 900px) {{ .banner-preview {{ align-items: flex-start; flex-direction: column; }} .pamphlet-grid {{ grid-template-columns: 1fr; }} .pamphlet-panel {{ min-height: auto; }} }}
</style>
</head>
<body>
{asset_body}
<section class="source-copy" id="details"><h2>Generated AI Content</h2><pre>{safe['result']}</pre></section>
</body>
</html>"""


def _create_visual_asset(result: str, form_data: dict[str, str]) -> dict[str, str] | None:
    """Create a downloadable HTML preview for supported visual assets."""
    content_type = form_data.get("content_type", "")
    if content_type not in VISUAL_ASSET_TYPES:
        return None

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    filename = _asset_filename(content_type)
    (GENERATED_DIR / filename).write_text(
        _render_asset_html(content_type, result, form_data),
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


def _build_prompt(form_data: dict[str, str]) -> Any:
    """Build an AI prompt using prompt_builder.py's public helper."""
    builder = _get_callable(
        prompt_builder,
        ("build_prompt", "create_prompt", "generate_prompt", "build_analysis_prompt"),
    )
    if builder is None:
        raise RuntimeError("prompt_builder.py does not expose a prompt builder function.")

    try:
        return builder(form_data)
    except TypeError:
        return builder(**form_data)


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
        prompt = _build_prompt(form_data)
        result = _run_analysis(prompt)
        asset = _create_visual_asset(str(result), form_data)
    except RuntimeError as exc:
        LOGGER.warning("Application configuration error: %s", exc)
        flash(str(exc), "error")
        return redirect(url_for("index"))
    except Exception:
        LOGGER.exception("Unexpected error while analyzing request")
        flash("We could not complete the analysis. Please try again.", "error")
        return redirect(url_for("index"))

    flash("Analysis completed successfully.", "success")
    return render_template("result.html", result=result, form_data=form_data, asset=asset)


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
