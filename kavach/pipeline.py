"""One Kavach session: transcripts in, risk updates, warnings and alerts out.

    Prisma transcripts ──> L1 keywords ──┐
            │ (finals)                    ├─> RiskScorer ──> spoken warning + family alert
            └────────> Evon (background) ─┘

The session consumes Transcript objects, so the same logic serves a live
microphone (Guardian), an Exotel call stream, or a recorded test call.
"""

import asyncio
import inspect
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass

from kavach.alerts.telegram import TelegramAlerter, format_alert
from kavach.debrief import build_debrief
from kavach.detect.evon import EvonClient
from kavach.detect.keywords import KeywordDetector
from kavach.detect.normalize import sanitize
from kavach.detect.scorer import Level, RiskScorer, RiskState
from kavach.speak.timbre import Audio, TimbreClient
from kavach.speak.warnings import ANNOUNCE, FAMILY_OPENER, warning_text
from kavach.stt.prisma import Transcript

log = logging.getLogger(__name__)

Speaker = Callable[[Audio], Awaitable[None]]
EventSink = Callable[[dict], Awaitable[None] | None]


@dataclass
class SessionConfig:
    language: str = "hi-IN"
    speak_sample_rate: int = 16000  # 8000 for telephone playback
    echo_guard: bool = True  # ignore transcripts while Kavach itself is speaking (mic mode)
    echo_tail_s: float = 1.0
    evon_window_lines: int = 40  # the call so far, capped for latency
    vote_samples: int = 3
    use_evon_warning: bool = False  # templates are reviewed and cached, so faster
    family_voice: dict | None = None  # cloned voice embedding


class KavachSession:
    def __init__(self, config: SessionConfig, detector: KeywordDetector, timbre: TimbreClient,
                 speaker: Speaker, evon: EvonClient | None = None,
                 alerter: TelegramAlerter | None = None, on_event: EventSink | None = None):
        self.config = config
        self.detector = detector
        self.timbre = timbre
        self.speaker = speaker
        self.evon = evon
        self.alerter = alerter
        self.on_event = on_event
        self.scorer = RiskScorer()
        self.lines: list[str] = []
        self.t0 = time.monotonic()
        self.speaking_until = 0.0
        self.first_flag_at: float | None = None
        self.warnings: list[dict] = []
        self.peak = RiskState(0, Level.NONE, [], [], 0, None, None)
        self._announced = False
        self._alerted = False
        self._speak_lock = asyncio.Lock()
        self._evon_task: asyncio.Task | None = None
        self._evon_dirty = False
        self._tasks: set[asyncio.Task] = set()
        self._partial = ""  # latest partial transcript of the utterance in progress
        self._seen_categories: set[str] = set()
        # When each milestone first happened (monotonic), to see where warning delay goes.
        self.timeline: dict[str, float] = {}

    def _mark(self, name: str, at: float | None = None) -> None:
        self.timeline.setdefault(name, at or time.monotonic())

    def _elapsed(self, now: float | None = None) -> float:
        return round((now or time.monotonic()) - self.t0, 2)

    async def _emit(self, event: dict) -> None:
        if self.on_event is None:
            return
        event = {"t": self._elapsed(), **event}
        result = self.on_event(event)
        if inspect.isawaitable(result):
            await result

    def _spawn(self, coro) -> None:
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def process(self, transcripts: AsyncIterator[Transcript]) -> dict:
        async for t in transcripts:
            await self.handle(t)
        while self._evon_task and not self._evon_task.done():
            await self._evon_task
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        report = self.report()
        debrief = build_debrief(report, self.config.language)
        if debrief:
            report["debrief"] = debrief
            await self._emit({"type": "debrief", **debrief})
        await self._emit({"type": "end", "report": report})
        return report

    async def handle(self, t: Transcript) -> None:
        now = time.monotonic()
        if self.config.echo_guard and now < self.speaking_until:
            await self._emit({"type": "ignored", "text": sanitize(t.text), "reason": "kavach speaking"})
            return
        hits = self.detector.scan(t.text)
        if hits and self.first_flag_at is None:
            self.first_flag_at = now
            self._mark("first_flag", now)
        self.scorer.add_hits(hits)
        new_categories = {h.category for h in hits} - self._seen_categories
        self._seen_categories |= new_categories
        await self._emit({
            "type": "transcript", "final": t.is_final, "text": sanitize(t.text),
            "flags": [{"category": h.category, "phrase": h.phrase} for h in hits],
        })
        if t.is_final and t.text.strip():
            self._partial = ""
            self.lines.append(t.text)
            self._schedule_evon()
        elif not t.is_final:
            self._partial = t.text
            if new_categories:
                # A new kind of red flag mid-sentence: ask Evon now instead of
                # waiting for the speaker to pause.
                self._schedule_evon()
        await self._update(now)

    def _schedule_evon(self) -> None:
        if self.evon is None:
            return
        if self._evon_task and not self._evon_task.done():
            self._evon_dirty = True  # re-run with the newer transcript when this one returns
            return
        self._evon_task = asyncio.create_task(self._run_evon())

    async def _run_evon(self) -> None:
        while True:
            self._evon_dirty = False
            lines = self.lines[-self.config.evon_window_lines:]
            if self._partial:
                lines = [*lines, self._partial]
            started = time.monotonic()
            if self.scorer.keyword_core_categories() >= 2:
                # Keywords already look like a scam: go straight to the vote (one
                # round trip instead of a single answer followed by a vote).
                verdict = await self.evon.assess_consistent(lines, self.config.language, self.config.vote_samples)
            else:
                verdict = await self.evon.assess(lines, self.config.language)
                if verdict.verdict == "SCAM" and not verdict.votes:
                    # Confirm before the scorer sees it: a transcript arriving mid-vote
                    # must not act on an unconfirmed SCAM (caused a false alarm in eval).
                    self._mark("evon_first_scam")
                    verdict = await self.evon.assess_consistent(lines, self.config.language, self.config.vote_samples)
            if verdict.verdict == "SCAM" and verdict.error is None:
                self._mark("evon_confirmed_scam")
            self.scorer.add_verdict(verdict)
            await self._emit({
                "type": "verdict", "verdict": verdict.verdict, "risk": verdict.risk,
                "scam_type": verdict.scam_type, "stage": verdict.stage, "votes": verdict.votes,
                "flags": [{"category": f.category, "evidence": f.evidence} for f in verdict.red_flags],
                "error": verdict.error, "latency_s": round(time.monotonic() - started, 2),
            })
            await self._update(time.monotonic())
            if not self._evon_dirty:
                return

    async def _update(self, now: float) -> None:
        state = self.scorer.evaluate(now)
        if state.risk >= self.peak.risk or state.level > self.peak.level:
            self.peak = state
        await self._emit({
            "type": "risk", "risk": state.risk, "level": state.level.name, "stages": state.stages,
            "categories": state.categories, "keyword_risk": state.keyword_risk,
            "evon_verdict": state.evon_verdict, "evon_risk": state.evon_risk,
        })
        if state.speak is not None:
            self._spawn(self._warn(state.speak, now))

    async def _warn(self, level: Level, triggered_at: float) -> None:
        verdict = self.scorer.verdict
        lang = self.config.language
        rate = self.config.speak_sample_rate
        parts: list[tuple[str, bool]] = []  # (text, use_family_voice)
        if level == Level.HARD and not self._announced:
            parts.append((ANNOUNCE.get(lang, ANNOUNCE["hi-IN"]), False))
            self._announced = True
        text = warning_text(level, lang, verdict.scam_type if verdict else "none",
                            verdict.warning if (verdict and self.config.use_evon_warning) else "")
        family = self.config.family_voice if level == Level.HARD else None
        if family:
            text = f"{FAMILY_OPENER.get(lang, '')} {text}".strip()
        parts.append((text, bool(family)))

        async with self._speak_lock:
            for part, cloned in parts:
                if cloned:
                    audio = await asyncio.to_thread(self.timbre.speak_cloned, part, family, rate)
                else:
                    audio = await asyncio.to_thread(self.timbre.speak, part, lang, None, rate)
                started = time.monotonic()
                self.speaking_until = started + audio.duration_s + self.config.echo_tail_s
                record = {
                    "level": level.name, "text": part, "family_voice": cloned,
                    "at_s": self._elapsed(started),
                    "after_trigger_s": round(started - triggered_at, 2),
                    "after_first_flag_s": round(started - self.first_flag_at, 2) if self.first_flag_at else None,
                }
                self.warnings.append(record)
                self._mark(f"warn_{level.name.lower()}", started)
                await self._emit({"type": "warning", **record})
                await self.speaker(audio)

        if level == Level.HARD and not self._alerted and self.alerter is not None:
            self._alerted = True
            flags = [(f.category, f.evidence) for f in (verdict.red_flags if verdict else [])]
            message = format_alert(verdict.scam_type if verdict else "none", self.peak.risk, flags,
                                   [sanitize(line) for line in self.lines])
            sent = await self.alerter.send(message)
            await self._emit({"type": "alert", "sent": sent, "message": message})

    def report(self) -> dict:
        v = self.scorer.verdict
        return {
            "duration_s": self._elapsed(),
            "language": self.config.language,
            "lines": [sanitize(line) for line in self.lines],
            "peak_risk": self.peak.risk,
            "level": self.scorer.level.name,
            "stages": self.peak.stages,
            "categories": self.peak.categories,
            "evon": None if v is None else {
                "verdict": v.verdict, "risk": v.risk, "scam_type": v.scam_type, "votes": v.votes,
                "flags": [{"category": f.category, "evidence": f.evidence} for f in v.red_flags],
            },
            "first_flag_at_s": self._elapsed(self.first_flag_at) if self.first_flag_at else None,
            "warnings": self.warnings,
            "timeline": {name: self._elapsed(at) for name, at in sorted(self.timeline.items(), key=lambda kv: kv[1])},
        }


class RecordingSpeaker:
    """Collects warning audio instead of playing it (tests, offline runs)."""

    def __init__(self):
        self.played: list[Audio] = []

    async def __call__(self, audio: Audio) -> None:
        self.played.append(audio)


async def transcripts_from_prisma(stream, source) -> AsyncIterator[Transcript]:
    async for t in stream.transcribe(source):
        yield t
