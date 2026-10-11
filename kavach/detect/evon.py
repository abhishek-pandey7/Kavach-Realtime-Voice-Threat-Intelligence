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
from difflib import SequenceMatcher
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
You get the transcript so far. Both speakers share one channel, so work out who the caller is
from what they say. Numbers such as OTPs and account numbers are masked as <OTP>, <ACCOUNT_NO>.

Decide whether the CALLER is scamming the person who received the call.

Rules:
1. SCAM: the caller asks the listener to send money, pay a fee or fine, share an OTP/PIN/CVV/
   password with the caller (an OTP is often described as "the code" or "the number that just
   came on your phone by SMS"; asking to read it out is the same as asking for the OTP), or
   install a remote-access app, AND uses pressure: fake authority
   (police, CBI, customs, bank, government), threats (arrest, case, account block, disconnection),
   urgency, or secrecy ("tell no one", "stay on the video call").
2. Also SCAM: someone claiming to be police/CBI/ED/customs says the listener is under "digital
   arrest" or will be arrested over the phone. Real police never do this.
3. UNCERTAIN: pressure or an official-sounding claim, but no request yet. Wait for more.
4. SAFE: normal calls, even if they mention parcels, OTPs, banks, payments or police. A delivery
   agent asking for the delivery OTP at the door is normal in India. A bank warning you NOT to share
   your OTP is normal. A family member asking for money without threats or secrecy is normal.

Scam types: {", ".join(SCAM_TYPES)}. Use digital_arrest when the caller claims police/CBI/customs
and threatens arrest, even if a parcel is mentioned.
Stages: {", ".join(STAGES)}, none.
Red-flag categories: {", ".join(CATEGORIES)}.

Reply with ONLY compact JSON, no other text:
{{"verdict":"SAFE|UNCERTAIN|SCAM","risk":0-100,"scam_type":"...","stage":"...","flags":[{{"category":"...","evidence":"2 to 6 words copied from the transcript"}}]}}
At most 4 flags. Copy evidence words exactly."""

# Worked examples (few-shot). Short on purpose: the shared prefix is cached by the server.
EXAMPLES = [
    (
        ["नमस्ते मैडम, मैं डिलीवरी बॉय बोल रहा हूं, आपका पार्सल लेकर आया हूं",
         "पार्सल देते समय आपके फोन पर जो ओटीपी आएगा वो मुझे दरवाजे पर बता दीजिएगा"],
        '{"verdict":"SAFE","risk":5,"scam_type":"none","stage":"none","flags":[]}',
    ),
    (
        ["मैं मुंबई कस्टम्स से बोल रहा हूं, आपके नाम के पार्सल में ड्रग्स मिले हैं",
         "आप डिजिटल अरेस्ट में हैं, यह बात किसी को मत बताना",
         "वेरिफिकेशन के लिए पैसे इस अकाउंट में ट्रांसफर कीजिए"],
        '{"verdict":"SCAM","risk":95,"scam_type":"digital_arrest","stage":"extraction","flags":'
        '[{"category":"fake_authority","evidence":"मुंबई कस्टम्स से बोल रहा"},'
        '{"category":"threat","evidence":"आप डिजिटल अरेस्ट में हैं"},'
        '{"category":"secrecy","evidence":"किसी को मत बताना"},'
        '{"category":"payment_demand","evidence":"पैसे इस अकाउंट में ट्रांसफर"}]}',
    ),
]


# Enforced by the server while generating (llama.cpp / vLLM structured output).
# maxLength on evidence stops the 4-bit model's occasional repetition loops when
# copying Devanagari, which otherwise run to the token limit and break the JSON.
EVIDENCE_MAX_CHARS = 60
VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"enum": list(VERDICTS)},
        "risk": {"type": "integer", "minimum": 0, "maximum": 100},
        "scam_type": {"enum": list(SCAM_TYPES)},
        "stage": {"enum": [*STAGES, "none"]},
        "flags": {
            "type": "array", "maxItems": 4,
            "items": {
                "type": "object",
                "properties": {
                    "category": {"enum": list(CATEGORIES)},
                    "evidence": {"type": "string", "maxLength": EVIDENCE_MAX_CHARS},
                },
                "required": ["category", "evidence"],
            },
        },
    },
    "required": ["verdict", "risk", "scam_type", "stage", "flags"],
}


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
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for example_lines, answer in EXAMPLES:
        example = "\n".join(f"{i + 1}. {line}" for i, line in enumerate(example_lines))
        messages.append({"role": "user", "content": f"Transcript so far:\n{example}"})
        messages.append({"role": "assistant", "content": answer})
    messages.append({"role": "user", "content": f"Listener's language: {lang}\nTranscript so far:\n{transcript}"})
    return messages


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


def _evidence_supported(evidence: str, transcript_norm: str, min_coverage: float = 0.7) -> bool:
    """True if the quote really comes from the transcript.

    The 4-bit Evon copies Hindi slightly imperfectly ("हजारी रपये" for "हजार
    रुपये"), so exact matching rejects genuine quotes. Instead, at least 70% of
    the quote's characters must appear in order in the transcript, counting
    only runs of 3+ characters so scattered letters don't add up.
    """
    ev = normalize(sanitize(evidence))
    if len(ev) < 3:
        return False
    if ev in transcript_norm:
        return True
    blocks = SequenceMatcher(None, ev, transcript_norm, autojunk=False).get_matching_blocks()
    covered = sum(b.size for b in blocks if b.size >= 3)
    return covered / len(ev) >= min_coverage


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
    for raw in obj.get("flags") or obj.get("red_flags") or []:
        if isinstance(raw, dict):
            category, evidence = raw.get("category"), str(raw.get("evidence", ""))
        elif isinstance(raw, (list, tuple)) and len(raw) == 2:
            category, evidence = raw[0], str(raw[1])
        else:
            continue
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
                 api_key: str | None = None, timeout_s: float = 10.0,
                 transport: httpx.AsyncBaseTransport | None = None):
        self.base_url = (base_url or os.environ.get("EVON_BASE_URL", "http://localhost:8000/v1")).rstrip("/")
        self.model = model or os.environ.get("EVON_MODEL", "model")
        key = api_key or os.environ.get("EVON_API_KEY")
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        self.timeout_s = timeout_s
        self.json_modes = ["schema", "object", None]  # fall back if the server rejects one
        self._http = httpx.AsyncClient(headers=headers, timeout=timeout_s, transport=transport)

    async def close(self) -> None:
        await self._http.aclose()

    async def _complete(self, messages: list[dict], temperature: float) -> str:
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": 0.95,
            "max_tokens": 256,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        mode = self.json_modes[0]
        if mode == "schema":
            body["response_format"] = {"type": "json_schema",
                                       "json_schema": {"name": "verdict", "schema": VERDICT_SCHEMA}}
        elif mode == "object":
            body["response_format"] = {"type": "json_object"}
        for attempt in range(3):
            try:
                resp = await self._http.post(f"{self.base_url}/chat/completions", json=body)
                break
            except httpx.ConnectError:
                # Seen on Windows: the tunnel's hostname intermittently fails to resolve
                # (getaddrinfo) for a few seconds while everything else works.
                if attempt == 2:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))
        if resp.status_code == 400 and len(self.json_modes) > 1:
            # The server doesn't support this response_format; try the next, simpler one.
            log.info("Evon server rejected response_format %r, falling back", mode)
            self.json_modes.pop(0)
            return await self._complete(messages, temperature)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"] or ""

    async def assess(self, lines: list[str], language: str = "hi-IN", temperature: float = 0.3) -> Verdict:
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
