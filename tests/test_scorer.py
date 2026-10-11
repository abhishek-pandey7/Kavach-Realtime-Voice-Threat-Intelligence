import pytest

from kavach.detect.evon import RedFlag, Verdict
from kavach.detect.keywords import KeywordDetector
from kavach.detect.scorer import Level, RiskScorer

SCAM_LINES = [
    "नमस्ते, मैं सी बी आई ऑफिस से बोल रहा हूं",
    "आपके नाम पर एक पार्सल में ड्रग्स मिले हैं, आपके खिलाफ अरेस्ट वारंट है",
    "यह बात किसी को मत बताना",
    "वेरिफिकेशन के लिए पैसे ट्रांसफर कीजिए",
]


@pytest.fixture(scope="module")
def detector():
    return KeywordDetector()


def feed(scorer, detector, lines):
    for line in lines:
        scorer.add_hits(detector.scan(line))


def test_keywords_alone_reach_soft_but_not_hard(detector):
    s = RiskScorer()
    feed(s, detector, SCAM_LINES)
    state = s.evaluate(now=0)
    assert state.level == Level.SOFT and state.speak == Level.SOFT
    assert state.stages == ["hook", "authority", "threat", "isolation", "extraction"]


def test_evon_scam_reaches_hard_and_speaks_once_per_level(detector):
    s = RiskScorer()
    feed(s, detector, SCAM_LINES)
    s.add_verdict(Verdict("SCAM", 92, "digital_arrest", "extraction", [RedFlag("threat", "ड्रग्स")]))
    first = s.evaluate(now=10)
    assert first.level == Level.HARD and first.speak == Level.HARD
    assert s.evaluate(now=20).speak is None  # cooldown
    assert s.evaluate(now=60).speak == Level.HARD  # repeat after 45 s


def test_evon_uncertain_never_speaks(detector):
    s = RiskScorer()
    feed(s, detector, SCAM_LINES[:2])
    s.add_verdict(Verdict("UNCERTAIN", 70))
    state = s.evaluate(now=0)
    assert state.risk < 65 and state.speak is None


def test_evon_safe_overrides_keyword_false_alarm(detector):
    s = RiskScorer()
    feed(s, detector, ["आपका पार्सल आज आएगा", "डिलीवरी पर ओटीपी बताइए", "पैसे ट्रांसफर कर दीजिए अगर कैश नहीं है"])
    s.add_verdict(Verdict("SAFE", 5))
    state = s.evaluate(now=0)
    assert state.level <= Level.WATCH and state.speak is None


def test_one_stage_repeated_is_not_enough(detector):
    s = RiskScorer()
    feed(s, detector, ["पुलिस", "पुलिस स्टेशन", "इंस्पेक्टर साहब", "क्राइम ब्रांच"])
    assert s.evaluate(now=0).level == Level.NONE


def test_failed_evon_call_is_ignored(detector):
    s = RiskScorer()
    s.add_verdict(Verdict(error="timeout"))
    assert s.verdict is None


def test_borderline_scam_needs_vote():
    s = RiskScorer()
    s.add_verdict(Verdict("SCAM", 75))
    assert s.needs_vote()
    s.add_verdict(Verdict("SCAM", 75, votes=["SCAM", "SCAM", "SAFE"]))
    assert not s.needs_vote()
