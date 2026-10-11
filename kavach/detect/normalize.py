"""Text normalisation and sanitisation applied before any detection.

Prisma writes Hindi in Devanagari, including English loanwords ("पार्सल",
"ड्रग्स") and sometimes spaces out acronyms ("सी बी आई"). Normalisation makes
lexicon matching robust to these variations. Sanitisation masks numbers that
look like OTPs, account numbers or IDs before text is logged or reasoned over
(see docs/RESEARCH.md, MASK).
"""

import re
import unicodedata

_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_PUNCT = re.compile(r"[।॥,.!?;:\"'“”‘’()\[\]{}…\-–—]+")
_SPACES = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Lowercases, unifies Devanagari variants and strips punctuation."""
    text = unicodedata.normalize("NFC", text).lower()
    text = text.translate(_DEVANAGARI_DIGITS)
    text = text.replace("़", "")  # nukta: ज़ -> ज
    text = text.replace("ँ", "ं")  # chandrabindu -> anusvara: हूँ -> हूं
    text = _PUNCT.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


# Amounts ("50000 रुपये", "₹ 20000") are a useful signal and not personal data,
# so digit runs next to a currency marker are left alone.
_NOT_AFTER_CURRENCY = r"(?<![\d₹])(?<!₹ )(?<!rs )(?<!rs\. )"
_NOT_BEFORE_CURRENCY = r"(?!\d)(?!\s*(?:रुपये|रुपए|रुपया|रु\b|rupees?\b|rs\b|₹|लाख|हजार|lakh|thousand))"

# Order matters: longer, more specific patterns first.
_MASKS = [
    ("<CARD_NO>", re.compile(r"(?<!\d)(?:\d[ -]?){15}\d(?!\d)")),
    ("<AADHAAR>", re.compile(r"(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)")),
    ("<PHONE>", re.compile(r"(?<!\d)(?:\+?91[ -]?)?[6-9]\d{9}(?!\d)")),
    ("<ACCOUNT_NO>", re.compile(_NOT_AFTER_CURRENCY + r"\d{9,18}" + _NOT_BEFORE_CURRENCY, re.IGNORECASE)),
    ("<OTP>", re.compile(_NOT_AFTER_CURRENCY + r"\d{4,8}" + _NOT_BEFORE_CURRENCY, re.IGNORECASE)),
]


def sanitize(text: str) -> str:
    """Replaces sensitive-looking digit sequences with tags like <OTP>."""
    text = text.translate(_DEVANAGARI_DIGITS)
    for tag, pattern in _MASKS:
        text = pattern.sub(tag, text)
    return text
