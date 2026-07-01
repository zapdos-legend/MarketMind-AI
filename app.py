"""Flask application entry point for MarketMind-AI.

This module keeps the web layer focused on request handling, validation, and
presentation while delegating prompt construction and AI analysis to the
project's helper modules.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable

from flask import Flask, flash, redirect, render_template, request, url_for

import ai_engine
import prompt_builder


LOGGER = logging.getLogger(__name__)
MAX_INPUT_LENGTH = int(os.environ.get("MAX_ANALYSIS_INPUT_LENGTH", "2000"))
REQUIRED_FORM_FIELDS = ("topic",)


app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key-change-me"),
    ENV=os.environ.get("FLASK_ENV", "production"),
)

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


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
    cleaned_data = {
        key: value.strip()
        for key, value in request.form.items()
        if isinstance(value, str) and value.strip()
    }
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
    except RuntimeError as exc:
        LOGGER.warning("Application configuration error: %s", exc)
        flash(str(exc), "error")
        return redirect(url_for("index"))
    except Exception:
        LOGGER.exception("Unexpected error while analyzing request")
        flash("We could not complete the analysis. Please try again.", "error")
        return redirect(url_for("index"))

    flash("Analysis completed successfully.", "success")
    return render_template("result.html", result=result, form_data=form_data)


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
