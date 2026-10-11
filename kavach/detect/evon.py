"""L2 detector: Gnani Evon v3.3 reasons over the call so far.

Evon is self-hosted behind an OpenAI-compatible endpoint (vLLM, SGLang or
llama.cpp server; see docs/EVON_HOSTING.md). Configure with:

    EVON_BASE_URL   e.g. http://localhost:8000/v1
    EVON_MODEL      served model name (default "model")
    EVON_API_KEY    optional bearer token

Design choices come from docs/RESEARCH.md:
- Evon sees the whole call so far, never one utterance (Shen et al. 2025).
- Verdicts are SAFE, UNCERTAIN or SCAM; Kavach never speaks on UNCERTAIN.
- Every red flag must quote the transcript; unsupported flags are dropped
  (hallucination guard, Shen et al. 2024).
- Each verdict names the tactic stage reached (Vishing-Tactics-Bench).
- Borderline cases can be sampled several times and majority-voted
  (self-consistency, Wang et al. 2023).
"""

import asyncio
import json
import logging
import os
import re
import statistics
from collections import Counter
from dataclasses import dataclass, field

import httpx

from kavach.detect.keywords import CATEGORIES, STAGES
from kavach.detect.normalize import normalize, sanitize

log = logging.getLogger(__name__)

VERDICTS = ("SAFE", "UNCERTAIN", "SCAM")
SCAM_TYPES = ("none", "digital_arrest", "courier_customs", "bank_kyc", "upi_refund",
              "relative_in_trouble", "utility_disconnection", "prize_job", "other")

LANGUAGE_NAMES = {
    "hi-IN": "Hindi", "en-IN": "English", "ta-IN": "Tamil", "bn-IN": "Bengali",
    "te-IN": "Telugu", "kn-IN": "Kannada", "ml-IN": "Malayalam", "mr-IN": "Marathi",
    "gu-IN": "Gujarati", "pa-IN": "Punjabi",
}

SYSTEM_PROMPT = f"""You are Kavach, a safety system listening to a live phone call in India.
You receive the transcript so far. Both speakers are mixed into one channel, so infer who
is the caller from what they say. Numbers like OTPs and account numbers are masked as tags
such as <OTP> or <ACCOUNT_NO>.

Decide whether the CALLER is running a scam on the person who received the call.

Common scams: fake police/CBI/ED/customs "digital arrest", parcel with drugs, bank or KYC
account block, UPI refund or money "sent by mistake", relative in trouble needing money,
electricity disconnection tonight, lottery/prize/job needing a fee, remote-access apps.
Scams usually move through stages: hook -> authority -> threat -> isolation -> extraction.

Genuine calls also mention banks, OTPs, parcels, payments and police. A real bank never asks
for an OTP, PIN or CVV; real police never arrest over a phone or video call; real delivery
agents ask for a delivery OTP only at the door. Do not flag a call just because such words
appear. Judge intent and pressure.

Return ONLY a JSON object, no other text:
{{
  "verdict": "SAFE" | "UNCERTAIN" | "SCAM",
  "risk": integer 0-100,
  "scam_type": one of {list(SCAM_TYPES)},
  "stage": the latest stage reached, one of {list(STAGES) + ["none"]},
  "red_flags": [{{"category": one of {list(CATEGORIES)}, "evidence": "exact words copied from the transcript"}}],
  "warning": "if SCAM: one or two short, calm sentences in the listener's language that name the trick, else empty"
}}
Use UNCERTAIN when there is not yet enough evidence either way. Keep evidence quotes short
and copied exactly. Use at most 5 red flags."""


@dataclass
class RedFlag:
    category: str
    evidence: str


@dataclass
class Verdict:
    verdict: str = "UNCERTAIN"
    risk: int = 0
    scam_type: str = "none"
    stage: str = "none"
    red_flags: list[RedFlag] = field(default_factory=list)
    warning: str = ""
    dropped_flags: int = 0  # flags removed because their evidence wasn't in the transcript
    votes: list[str] = field(default_factory=list)
    error: str | None = None


def build_messages(lines: list[str], language: str) -> list[dict]:
    transcript = "\n".join(f"{i + 1}. {sanitize(line)}" for i, line in enumerate(lines))
    lang = LANGUAGE_NAMES.get(language, "the caller's language")
    user = f"Listener's language: {lang}\n\nTranscript so far:\n{transcript}"
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def extract_json(content: str) -> dict:
    """Pulls the first JSON object out of a model reply (tolerates think blocks and fences)."""
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    start = content.find("{")
    if start < 0:
        raise ValueError("no JSON object in reply")
    obj, _ = json.JSONDecoder().raw_decode(content[start:])
    if not isinstance(obj, dict):
        raise ValueError("reply JSON is not an object")
    return obj


def _evidence_supported(evidence: str, transcript_norm: str) -> bool:
    ev = normalize(sanitize(evidence))
    if not ev:
        return False
    if ev in transcript_norm:
        return True
    words = ev.split()
    present = sum(1 for w in words if w in transcript_norm)
    return len(words) >= 2 and present / len(words) >= 0.7


def parse_verdict(obj: dict, lines: list[str]) -> Verdict:
    """Validates a raw model object and applies the evidence guard."""
    transcript_norm = normalize(sanitize(" ".join(lines)))
    verdict = str(obj.get("verdict", "UNCERTAIN")).upper()
    verdict = verdict if verdict in VERDICTS else "UNCERTAIN"
    try:
        risk = max(0, min(100, int(round(float(obj.get("risk", 0))))))
    except (TypeError, ValueError):
        risk = 0
    scam_type = obj.get("scam_type") if obj.get("scam_type") in SCAM_TYPES else "other"
    stage = obj.get("stage") if obj.get("stage") in STAGES else "none"

    flags, dropped = [], 0
    for raw in obj.get("red_flags") or []:
        if not isinstance(raw, dict):
            continue
        category, evidence = raw.get("category"), str(raw.get("evidence", ""))
        if category in CATEGORIES and _evidence_supported(evidence, transcript_norm):
            flags.append(RedFlag(category, evidence))
        else:
            dropped += 1

    if verdict == "SCAM" and not flags:
        # A scam verdict with no checkable evidence is not trusted.
        verdict, risk = "UNCERTAIN", min(risk, 60)
    warning = str(obj.get("warning") or "") if verdict == "SCAM" else ""
    return Verdict(verdict, risk, scam_type if verdict != "SAFE" else "none", stage, flags, warning, dropped)


def majority(verdicts: list[Verdict]) -> Verdict:
    """Self-consistency: majority verdict, median risk, flags from agreeing samples."""
    ok = [v for v in verdicts if v.error is None]
    if not ok:
        return verdicts[0] if verdicts else Verdict(error="no samples")
    counts = Counter(v.verdict for v in ok)
    top, n = counts.most_common(1)[0]
    if n <= len(ok) / 2:
        top = "UNCERTAIN"
    agreeing = [v for v in ok if v.verdict == top] or ok
    best = max(agreeing, key=lambda v: len(v.red_flags))
    return Verdict(
        verdict=top,
        risk=int(statistics.median(v.risk for v in ok)),
        scam_type=best.scam_type,
        stage=best.stage,
        red_flags=best.red_flags,
        warning=best.warning if top == "SCAM" else "",
        dropped_flags=sum(v.dropped_flags for v in ok),
        votes=[v.verdict for v in ok],
    )


class EvonClient:
    def __init__(self, base_url: str | None = None, model: str | None = None,
                 api_key: str | None = None, timeout_s: float = 6.0,
                 transport: httpx.AsyncBaseTransport | None = None):
        self.base_url = (base_url or os.environ.get("EVON_BASE_URL", "http://localhost:8000/v1")).rstrip("/")
        self.model = model or os.environ.get("EVON_MODEL", "model")
        key = api_key or os.environ.get("EVON_API_KEY")
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        self.timeout_s = timeout_s
        self.json_mode = True
        self._http = httpx.AsyncClient(headers=headers, timeout=timeout_s, transport=transport)

    async def close(self) -> None:
        await self._http.aclose()

    async def _complete(self, messages: list[dict], temperature: float) -> str:
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": 0.95,
            "max_tokens": 400,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        if self.json_mode:
            body["response_format"] = {"type": "json_object"}
        resp = await self._http.post(f"{self.base_url}/chat/completions", json=body)
        if resp.status_code == 400 and self.json_mode:
            # Some servers don't support response_format; retry once without it.
            self.json_mode = False
            return await self._complete(messages, temperature)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"] or ""

    async def assess(self, lines: list[str], language: str = "hi-IN", temperature: float = 0.6) -> Verdict:
        messages = build_messages(lines, language)
        try:
            content = await asyncio.wait_for(self._complete(messages, temperature), self.timeout_s)
            return parse_verdict(extract_json(content), lines)
        except (httpx.HTTPError, asyncio.TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
            log.warning("Evon assessment failed: %r", exc)
            return Verdict(error=repr(exc))

    async def assess_consistent(self, lines: list[str], language: str = "hi-IN", samples: int = 3) -> Verdict:
        results = await asyncio.gather(*(self.assess(lines, language) for _ in range(samples)))
        return majority(list(results))
