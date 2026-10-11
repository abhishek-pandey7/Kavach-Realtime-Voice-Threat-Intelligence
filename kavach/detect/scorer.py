"""Fuses L1 keyword hits and L2 Evon verdicts into a risk level for the call.

Escalation ladder:
    WATCH  risk >= 40  dashboard only, nothing audible
    SOFT   risk >= 65  short spoken caution to the user; needs two or more
                       distinct non-hook red-flag categories
    HARD   risk >= 85  announcement into the call + family alert; needs an
                       Evon SCAM verdict (keywords alone never reach HARD)

Rules from docs/RESEARCH.md:
- Progression through tactic stages adds risk; repeating one stage doesn't.
- Evon UNCERTAIN means "no opinion yet": Kavach behaves as if Evon were
  absent (keywords can reach SOFT, never HARD) and ignores Evon's risk number
  and flags. Capping UNCERTAIN below SOFT muted keyword warnings on two real
  scams, and counting its risk caused a false alarm (evaluation, Oct 11).
- Evon SAFE overrides keyword false alarms (capped below SOFT).
- If Evon is unavailable, keywords alone can reach SOFT but not HARD.
- Levels only rise within a call; HARD is repeated at most every 45 s.
"""

from dataclasses import dataclass, field
from enum import IntEnum

from kavach.detect.evon import Verdict
from kavach.detect.keywords import Hit, l1_score, stages


class Level(IntEnum):
    NONE = 0
    WATCH = 1
    SOFT = 2
    HARD = 3


WATCH_AT, SOFT_AT, HARD_AT = 40, 65, 85
HARD_REPEAT_S = 45.0

# Bonus for distinct non-hook stages seen (authority, threat, isolation, extraction).
_STAGE_BONUS = {0: 0, 1: 0, 2: 10, 3: 20, 4: 30}


@dataclass
class RiskState:
    risk: int
    level: Level
    stages: list[str]
    categories: list[str]
    keyword_risk: int
    evon_verdict: str | None
    evon_risk: int | None
    speak: Level | None = None  # set when a warning should be spoken now


@dataclass
class RiskScorer:
    hits: dict[tuple[str, str], Hit] = field(default_factory=dict)
    verdict: Verdict | None = None
    level: Level = Level.NONE
    last_spoken: dict[Level, float] = field(default_factory=dict)

    def add_hits(self, hits: list[Hit]) -> None:
        for h in hits:
            self.hits.setdefault((h.category, h.phrase), h)

    def add_verdict(self, verdict: Verdict) -> None:
        if verdict.error is None:
            self.verdict = verdict

    def keyword_risk(self) -> int:
        hits = list(self.hits.values())
        core = [s for s in stages(hits) if s != "hook"]
        risk = 80 * l1_score(hits) + _STAGE_BONUS[min(len(core), 4)]
        return int(round(min(risk, 100)))

    def evaluate(self, now: float) -> RiskState:
        hits = list(self.hits.values())
        kw = self.keyword_risk()
        v = self.verdict
        opinion = v if v is not None and v.verdict in ("SCAM", "SAFE") else None
        if opinion is None:  # no Evon, or UNCERTAIN: keywords decide, never HARD
            risk = min(kw, HARD_AT - 1)
        elif opinion.verdict == "SCAM":
            risk = max(opinion.risk, kw)
        else:  # SAFE overrides keyword false alarms
            risk = min(kw, SOFT_AT - 1)

        categories = sorted({h.category for h in hits} | {f.category for f in (opinion.red_flags if opinion else [])})
        core_categories = {c for c in categories if c not in ("hook", "too_good")}

        level = Level.NONE
        if risk >= WATCH_AT:
            level = Level.WATCH
        if risk >= SOFT_AT and len(core_categories) >= 2:
            level = Level.SOFT
        if risk >= HARD_AT and v is not None and v.verdict == "SCAM":
            level = Level.HARD

        speak = None
        if level > self.level and level >= Level.SOFT:
            speak = level
        elif level == Level.HARD and now - self.last_spoken.get(Level.HARD, -1e9) >= HARD_REPEAT_S:
            speak = Level.HARD
        if speak is not None:
            self.last_spoken[speak] = now
        self.level = max(self.level, level)

        all_stages = stages(hits)
        if v is not None and v.stage not in ("none", *all_stages):
            all_stages = [s for s in ("hook", "authority", "threat", "isolation", "extraction")
                          if s in set(all_stages) | {v.stage}]
        return RiskState(
            risk=risk, level=self.level, stages=all_stages, categories=categories,
            keyword_risk=kw, evon_verdict=v.verdict if v else None,
            evon_risk=v.risk if v else None, speak=speak,
        )

    def needs_vote(self) -> bool:
        """A SCAM verdict must survive a self-consistency vote before it can reach HARD.

        On Evon v3.3 a single sample sometimes flips to SCAM for one turn of a
        genuine call (seen on a real bank fraud-alert script), so every unvoted
        SCAM verdict is re-checked with a majority of several samples.
        """
        v = self.verdict
        return v is not None and v.verdict == "SCAM" and not v.votes
