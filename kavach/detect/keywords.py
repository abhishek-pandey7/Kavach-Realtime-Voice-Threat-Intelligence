"""L1 detector: instant, explainable red-flag matching over transcripts.

Lexicons live in kavach/detect/lexicon/<lang>.yml. All lexicons are applied
to every transcript, since a Hindi call can be transcribed in Devanagari or
Latin script and scammers switch languages mid-call.

Categories follow scam-psychology principles (Stajano and Wilson, 2011) and
map onto tactic stages, so the risk scorer can reward progression through a
scam rather than repeated hits on one stage (see docs/RESEARCH.md).
"""

import math
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from kavach.detect.normalize import normalize, sanitize

LEXICON_DIR = Path(__file__).parent / "lexicon"

# Order of stages in a typical scam call.
STAGES = ("hook", "authority", "threat", "isolation", "extraction")


@dataclass(frozen=True)
class Category:
    stage: str
    weight: float  # contribution to the L1 score, 0..1


CATEGORIES = {
    "hook": Category("hook", 0.10),
    "too_good": Category("hook", 0.20),
    "fake_authority": Category("authority", 0.30),
    "threat": Category("threat", 0.35),
    "urgency": Category("threat", 0.15),
    "secrecy": Category("isolation", 0.40),
    "payment_demand": Category("extraction", 0.40),
    "credential_request": Category("extraction", 0.45),
    "remote_access": Category("extraction", 0.45),
}


@dataclass(frozen=True)
class Hit:
    category: str
    stage: str
    weight: float
    phrase: str  # the matched text, after normalisation
    language: str


def _compile_entry(entry: str) -> str:
    is_regex = entry.startswith("re:")
    if is_regex:
        body = entry[3:].strip().lower()
    else:
        body = r"\s*".join(re.escape(part) for part in normalize(entry).split(" "))
    if body.isascii() and re.search(r"[a-z]", body):
        # Latin words need word boundaries ("rbi" must not match "turbine").
        # Regex entries are often stems ("bata" in "batana"), so they only
        # get a leading boundary.
        trailing = "" if is_regex else "(?![a-z0-9])"
        body = rf"(?<![a-z0-9])(?:{body}){trailing}"
    return body


def load_lexicons(directory: Path = LEXICON_DIR) -> dict[tuple[str, str], re.Pattern]:
    """Returns one compiled alternation per (language, category)."""
    compiled = {}
    for path in sorted(directory.glob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for category, entries in data.items():
            if category not in CATEGORIES:
                raise ValueError(f"{path.name}: unknown category {category!r}")
            alternation = "|".join(f"(?:{_compile_entry(e)})" for e in entries)
            compiled[(path.stem, category)] = re.compile(alternation)
    return compiled


class KeywordDetector:
    def __init__(self, directory: Path = LEXICON_DIR):
        self.patterns = load_lexicons(directory)

    def scan(self, text: str) -> list[Hit]:
        """Returns one hit per distinct matched phrase."""
        clean = normalize(sanitize(text))
        hits, seen = [], set()
        for (language, category), pattern in self.patterns.items():
            meta = CATEGORIES[category]
            for match in pattern.finditer(clean):
                key = (category, match.group(0))
                if key not in seen:
                    seen.add(key)
                    hits.append(Hit(category, meta.stage, meta.weight, match.group(0), language))
        return hits


def l1_score(hits: list[Hit]) -> float:
    """Noisy-OR over distinct categories: several kinds of red flag add up,
    repeating one kind does not."""
    best: dict[str, float] = {}
    for hit in hits:
        best[hit.category] = max(best.get(hit.category, 0.0), hit.weight)
    return 1.0 - math.prod(1.0 - w for w in best.values())


def stages(hits: list[Hit]) -> list[str]:
    """Distinct tactic stages present, in scam order."""
    present = {hit.stage for hit in hits}
    return [s for s in STAGES if s in present]
