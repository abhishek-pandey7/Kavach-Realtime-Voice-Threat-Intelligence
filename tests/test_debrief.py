from datetime import datetime

from kavach.debrief import build_debrief

HARD_REPORT = {
    "level": "HARD", "duration_s": 52.4, "categories": ["fake_authority", "threat", "secrecy", "hook"],
    "evon": {"verdict": "SCAM", "scam_type": "digital_arrest", "risk": 95, "votes": ["SCAM"] * 3,
             "flags": [{"category": "threat", "evidence": "आप डिजिटल अरेस्ट में हैं"},
                       {"category": "payment_demand", "evidence": "पैसे इस अकाउंट में ट्रांसफर"}]},
}


def test_no_debrief_for_calls_that_were_not_flagged():
    assert build_debrief({"level": "WATCH", "categories": ["hook"]}) is None


def test_hindi_debrief_names_the_scam_and_the_tricks():
    d = build_debrief(HARD_REPORT, "hi-IN", when=datetime(2026, 10, 12, 18, 30))
    assert "डिजिटल अरेस्ट" in d["summary"]
    assert "पैसे भेजने" in d["summary"] and "किसी को न बताने" in d["summary"]
    assert any("1930" in step for step in d["next_steps"])


def test_complaint_draft_quotes_evidence_and_never_claims_filing():
    d = build_debrief(HARD_REPORT, "hi-IN", when=datetime(2026, 10, 12, 18, 30))
    draft = d["complaint_draft"]
    assert "12 Oct 2026, 06:30 PM" in draft
    assert '"आप डिजिटल अरेस्ट में हैं"' in draft
    assert "has not filed anything" in draft and "<fill in" in draft


def test_soft_warning_without_evon_uses_keyword_categories():
    d = build_debrief({"level": "SOFT", "categories": ["fake_authority", "credential_request"], "evon": None}, "en-IN")
    assert "suspicious" in d["summary"] and "OTP" in d["summary"]
