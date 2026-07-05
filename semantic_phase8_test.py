"""Semantic smoke tests for Phase 8 copy intelligence."""
from __future__ import annotations

import copy_engine
import industry_engine

CASES = [
    ("CarePlus Clinic", {"content_type":"Poster","topic":"Promote a free health checkup camp for families and senior citizens.","business_name":"CarePlus Clinic","product_service":"Health Checkup Camp","audience":"Families and Senior Citizens","platform":"Facebook","tone":"Trustworthy, Caring, Professional","offer":"Free BP, Sugar and BMI Screening","notes":"Use healthcare-focused messaging. Show doctors, patients and medical trust. Include Book Appointment CTA."}, "healthcare", ["health", "screen", "checkup", "care"], ["fitness", "app", "pizza", "apartment"]),
    ("Skyline Residences", {"content_type":"Poster","topic":"Promote premium apartments for modern families.","business_name":"Skyline Residences","product_service":"Luxury Apartments","audience":"Home Buyers","platform":"Instagram","tone":"Premium, Luxury, Aspirational","offer":"Free Site Visit","notes":"Focus on luxury living, spacious homes and premium lifestyle. Include Schedule Site Visit CTA."}, "real_estate", ["home", "living", "premium"], ["food", "clinic", "fitness", "coffee"]),
    ("BrewNest Café", {"content_type":"Poster","topic":"Promote a breakfast and coffee combo for busy professionals.","business_name":"BrewNest Café","product_service":"Coffee and Breakfast Combo","audience":"Office Workers","platform":"Instagram","tone":"Warm, Cozy, Friendly","offer":"Coffee + Sandwich Combo at ₹149","notes":"Show coffee cups, breakfast food and morning energy. Include Visit Today CTA."}, "cafe_food", ["coffee", "breakfast", "morning"], ["show coffee cups", "pizza", "doctor", "apartment", "gym"]),
    ("FitRush", {"content_type":"Poster","topic":"Launch a fitness tracking app for college students.","business_name":"FitRush","product_service":"Fitness App","audience":"College Students","platform":"Instagram","tone":"Energetic, Motivational","offer":"Free 7-Day Trial","notes":"Show fitness tracking, workout progress and student lifestyle. Include Download App CTA."}, "fitness_app", ["fitness", "college", "workout", "app"], ["clinic", "real estate", "cafe", "site visit"]),
    ("SkillForge Academy", {"content_type":"Poster","topic":"Promote an AI and Data Science career program.","business_name":"SkillForge Academy","product_service":"AI Career Program","audience":"Students and Fresh Graduates","platform":"LinkedIn","tone":"Professional, Ambitious","offer":"Early Bird Scholarship","notes":"Show certification, mentorship, learning roadmap and career growth. Include Enroll Now CTA."}, "edtech", ["ai", "data", "career", "skill"], ["exam readiness", "clinic", "gym", "apartment", "pizza"]),
]

def assert_case(name, form, industry, expected_terms, forbidden_terms):
    alignment = industry_engine.build_industry_alignment(form)
    strategy = copy_engine.generate_copy_strategy(form, industry_alignment=alignment)
    blob = " ".join(str(v) for v in strategy.values()).lower()
    assert alignment["detected_industry"] == industry, (name, alignment["detected_industry"])
    assert strategy["detected_industry"] == industry, (name, strategy["detected_industry"])
    assert any(term in blob for term in expected_terms), (name, strategy)
    for term in forbidden_terms:
        assert term not in strategy["primary_headline"].lower(), (name, term, strategy["primary_headline"])
        assert term not in strategy["offer_line"].lower(), (name, term, strategy["offer_line"])
    if name == "BrewNest Café":
        assert strategy["offer_line"] == "Coffee + Sandwich Combo at ₹149", strategy["offer_line"]
        assert "show coffee cups" not in strategy["offer_line"].lower()
        assert "show coffee cups" not in strategy["primary_headline"].lower()
    if name == "SkillForge Academy":
        assert "exam readiness" not in blob
    print(f"PASS {name}: {strategy['primary_headline']} / {strategy['cta_primary']}")

for case in CASES:
    assert_case(*case)
