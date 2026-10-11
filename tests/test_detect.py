import pytest

from kavach.detect.keywords import KeywordDetector, l1_score, stages
from kavach.detect.normalize import normalize, sanitize


@pytest.fixture(scope="module")
def detector():
    return KeywordDetector()


def categories(hits):
    return {h.category for h in hits}


def test_normalize_unifies_devanagari_variants():
    assert normalize("बोल रहा हूँ। ज़रूरी") == "बोल रहा हूं जरूरी"


@pytest.mark.parametrize("text,expected", [
    ("OTP 482913 batao", "OTP <OTP> batao"),
    ("call 9876543210", "call <PHONE>"),
    ("aadhaar 1234 5678 9012", "aadhaar <AADHAAR>"),
    ("card 4111 1111 1111 1111", "card <CARD_NO>"),
    ("50000 रुपये भेजो", "50000 रुपये भेजो"),
    ("₹ 20000 transfer", "₹ 20000 transfer"),
    ("account 50123456789 me 25000 rupees", "account <ACCOUNT_NO> me 25000 rupees"),
])
def test_sanitize_masks_ids_but_keeps_amounts(text, expected):
    assert sanitize(text) == expected


def test_digital_arrest_script_hits_several_stages(detector):
    # Exact Prisma output for our Timbre test clip (spaced acronym included).
    text = "नमस्ते, मैं सी बी आई ऑफिस से बोल रहा हूँ, आपके नाम पर एक पार्सल में ड्रग्स मिले हैं, यह बात किसी को मत बताना।"
    hits = detector.scan(text)
    assert {"fake_authority", "threat", "secrecy", "hook"} <= categories(hits)
    assert stages(hits) == ["hook", "authority", "threat", "isolation"]
    assert l1_score(hits) > 0.65


def test_joined_acronym_also_matches(detector):
    assert "fake_authority" in categories(detector.scan("मैं सीबीआई से बोल रहा हूं"))


def test_hinglish_latin_script(detector):
    hits = detector.scan("Main Mumbai police se bol raha hoon, aapke naam pe digital arrest warrant hai, kisi ko mat batana")
    assert {"fake_authority", "threat", "secrecy"} <= categories(hits)


def test_otp_request_is_caught_after_masking(detector):
    hits = detector.scan("Sir please aapke phone pe 482913 aaya hai, woh bata dijiye")
    assert "credential_request" in categories(hits)


@pytest.mark.parametrize("text", [
    "नमस्ते, मैं आपकी बेटी बोल रही हूं, आज शाम को खाने पर आ रही हूं",
    "आपका कस्टमर केयर कॉल है, आपकी शिकायत दर्ज हो गई है",
    "The turbine at the plant needs a check this weekend",
])
def test_benign_calls_score_low(detector, text):
    assert l1_score(detector.scan(text)) < 0.4


def test_delivery_with_otp_is_below_soft_warning(detector):
    # A genuine delivery call: a hard negative. L1 alone must not reach a warning.
    text = "आपका पार्सल आज डिलीवर होगा, डिलीवरी के समय ओटीपी डिलीवरी बॉय को बताइए"
    assert l1_score(detector.scan(text)) < 0.65


def test_tamil_and_bengali_drafts_load(detector):
    assert "threat" in categories(detector.scan("நீங்கள் கைது செய்யப்படுவீர்கள்"))
    assert "secrecy" in categories(detector.scan("এই কথা কাউকে বলবেন না"))


def test_call_transfer_is_not_a_payment_demand(detector):
    hits = detector.scan("मैं आपकी कॉल सीबीआई ऑफिसर को ट्रांसफर कर रहा हूँ")
    assert "payment_demand" not in categories(hits)
    assert "payment_demand" in categories(detector.scan("सारे पैसे इस अकाउंट में ट्रांसफर कीजिए"))


def test_otp_described_without_the_word(detector):
    hits = detector.scan("आपके फोन पर अभी छह अंकों का एक संदेश आएगा, बस वो अंक मुझे पढ़कर सुना दीजिए")
    assert "credential_request" in categories(hits)
    # A genuine "don't share the code" message must not count as a request in a way that warns alone.
    assert l1_score(detector.scan("बैंक कभी कोड नहीं मांगता")) < 0.4
