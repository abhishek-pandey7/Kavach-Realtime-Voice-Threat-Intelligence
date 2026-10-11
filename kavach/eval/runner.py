"""Runs Kavach over scripted calls under several audio conditions and scores it.

Metrics (docs/RESEARCH.md, Evaluation):
- scam recall: scam calls that got a SOFT or HARD warning
- false alarm rate: genuine calls that got a SOFT or HARD warning
- time to warn: first warning time, from call start and from the first red flag
- CER: character error rate of Prisma's transcript against the script
"""

import asyncio
import statistics
import time
import wave
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import yaml

from kavach.audio.sources import file_source
from kavach.config import CACHE_DIR
from kavach.detect.keywords import KeywordDetector
from kavach.detect.normalize import normalize
from kavach.eval import degrade
from kavach.pipeline import KavachSession, RecordingSpeaker, SessionConfig
from kavach.stt.prisma import PrismaConfig, PrismaStream

EVAL_DIR = CACHE_DIR / "eval"
NOISE_DIR = CACHE_DIR / "noise"

# name -> (sample rate streamed to Prisma, SNR in dB or None, telephone channel?)
CONDITIONS = {
    "clean16k": (16000, None, False),
    "phone": (8000, None, True),
    "phone_snr10": (8000, 10.0, True),
    "phone_snr5": (8000, 5.0, True),
    "phone_snr0": (8000, 0.0, True),
}


@dataclass
class CallResult:
    call_id: str
    label: str
    scam_type: str
    condition: str
    level: str
    peak_risk: int
    warned: bool
    hard: bool
    first_warning_s: float | None
    after_first_flag_s: float | None
    evon_verdict: str | None
    cer: float
    transcript: str
    error: str | None = None


def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cer(reference: str, hypothesis: str) -> float:
    ref = normalize(reference).replace(" ", "")
    hyp = normalize(hypothesis).replace(" ", "")
    return edit_distance(ref, hyp) / max(len(ref), 1)


def _noise_for(index: int, n: int, sample_rate: int) -> np.ndarray:
    files = sorted(NOISE_DIR.glob("*.wav")) if NOISE_DIR.exists() else []
    if files:
        return degrade.file_noise(files[index % len(files)], n, sample_rate)
    # No recorded noise yet: pink noise plus mains hum as a stand-in.
    return degrade.generated_noise("pink", n, sample_rate, seed=index) + \
        0.3 * degrade.generated_noise("hum", n, sample_rate)


def prepare_audio(call_wav: Path, call_id: str, condition: str, index: int) -> tuple[Path, int]:
    rate, snr, phone = CONDITIONS[condition]
    out = EVAL_DIR / "audio" / f"{call_id}__{condition}.wav"
    if out.exists():
        return out, rate
    x = degrade.load(call_wav, 16000)
    if snr is not None:
        x = degrade.add_noise(x, _noise_for(index, len(x), 16000), snr)
    if phone:
        x = degrade.telephone(x, 16000)
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(degrade.to_pcm16(x))
    return out, rate


async def run_one(script: dict, call_wav: Path, condition: str, index: int, api_key: str,
                  detector: KeywordDetector, timbre, evon=None) -> CallResult:
    path, _ = prepare_audio(call_wav, script["id"], condition, index)
    language = script["language"]
    reference = " ".join(text for _, text in script["turns"])
    for attempt in range(2):  # retry once if Prisma returns nothing (seen once under load)
        session = KavachSession(SessionConfig(language=language, echo_guard=False), detector, timbre,
                                RecordingSpeaker(), evon=evon)
        prisma = PrismaStream(api_key, PrismaConfig(language=language))
        try:
            report = await session.process(prisma.transcribe(file_source(path, 16000)))
            error = None
        except Exception as exc:  # keep the batch going
            report, error = session.report(), repr(exc)
        if report["lines"]:
            break
        error = error or "empty transcript"
    hypothesis = " ".join(report["lines"])
    first = report["warnings"][0] if report["warnings"] else None
    return CallResult(
        call_id=script["id"], label=script["label"], scam_type=script.get("scam_type", "none"),
        condition=condition, level=report["level"], peak_risk=report["peak_risk"],
        warned=report["level"] in ("SOFT", "HARD"), hard=report["level"] == "HARD",
        first_warning_s=first["at_s"] if first else None,
        after_first_flag_s=first["after_first_flag_s"] if first else None,
        evon_verdict=report["evon"]["verdict"] if report["evon"] else None,
        cer=round(cer(reference, hypothesis), 3), transcript=hypothesis, error=error,
    )


async def run_all(scripts: list[tuple[dict, Path]], conditions: list[str], api_key: str, timbre,
                  evon=None, concurrency: int = 3) -> list[CallResult]:
    detector = KeywordDetector()
    gate = asyncio.Semaphore(concurrency)

    async def guarded(i, script, wav, condition):
        async with gate:
            started = time.monotonic()
            result = await run_one(script, wav, condition, i, api_key, detector, timbre, evon)
            print(f"  {script['id']:<28} {condition:<12} {result.level:<5} risk={result.peak_risk:<3} "
                  f"CER={result.cer:.2f} ({time.monotonic() - started:.0f}s)")
            return result

    jobs = [guarded(i, s, w, c) for i, (s, w) in enumerate(scripts) for c in conditions]
    return list(await asyncio.gather(*jobs))


def load_script(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def summarise(results: list[CallResult]) -> list[dict]:
    rows = []
    for condition in dict.fromkeys(r.condition for r in results):
        rs = [r for r in results if r.condition == condition]
        scams = [r for r in rs if r.label == "scam"]
        genuine = [r for r in rs if r.label != "scam"]
        times = [r.first_warning_s for r in scams if r.first_warning_s is not None]
        lags = [r.after_first_flag_s for r in scams if r.after_first_flag_s is not None]
        rows.append({
            "condition": condition,
            "scam_calls": len(scams),
            "recall": sum(r.warned for r in scams) / len(scams) if scams else None,
            "hard_rate": sum(r.hard for r in scams) / len(scams) if scams else None,
            "genuine_calls": len(genuine),
            "false_alarm_rate": sum(r.warned for r in genuine) / len(genuine) if genuine else None,
            "median_warn_s": statistics.median(times) if times else None,
            "median_after_flag_s": statistics.median(lags) if lags else None,
            "mean_cer": statistics.mean(r.cer for r in rs) if rs else None,
        })
    return rows


def _pct(v):
    return "–" if v is None else f"{v * 100:.0f}%"


def _sec(v):
    return "–" if v is None else f"{v:.1f} s"


def write_report(results: list[CallResult], path: Path, evon_used: bool) -> None:
    rows = summarise(results)
    lines = [
        "# Kavach evaluation report",
        "",
        f"Generated {time.strftime('%Y-%m-%d %H:%M')}. Evon: {'on' if evon_used else 'off (keywords only, so HARD is impossible by design)'}.",
        f"{len({r.call_id for r in results})} scripted calls, all synthetic (voiced with Timbre v2.5). "
        "Small sample: treat these numbers as a smoke test, not a benchmark.",
        "",
        "Conditions: `clean16k` original audio; `phone` 8 kHz, 300 to 3400 Hz, G.711 mu-law; "
        "`phone_snrN` noise mixed at N dB SNR before the phone channel. All audio is streamed to "
        "Prisma at 16 kHz (phone conditions are band-limited first).",
        "",
        "Noise: " + (f"recorded files from cache/noise/ ({len(list(NOISE_DIR.glob('*.wav')))} files)."
                     if NOISE_DIR.exists() and any(NOISE_DIR.glob('*.wav'))
                     else "generated pink noise plus 50 Hz mains hum. No recorded noise yet, so real-world "
                          "noise (traffic, TV, crowds) may be harder than these numbers suggest."),
        "",
        "## Summary",
        "",
        "| Condition | Scam recall | HARD rate | False alarms | Median first warning | Median after first red flag | Mean CER |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['condition']} | {_pct(r['recall'])} ({r['scam_calls']} calls) | {_pct(r['hard_rate'])} | "
                     f"{_pct(r['false_alarm_rate'])} ({r['genuine_calls']} calls) | {_sec(r['median_warn_s'])} | "
                     f"{_sec(r['median_after_flag_s'])} | {r['mean_cer']:.3f} |")
    lines += ["", "## Per call", "",
              "| Call | Label | Condition | Level | Peak risk | First warning | Evon | CER |",
              "|---|---|---|---|---|---|---|---|"]
    for r in sorted(results, key=lambda r: (r.call_id, r.condition)):
        lines.append(f"| {r.call_id} | {r.label} | {r.condition} | {r.level} | {r.peak_risk} | "
                     f"{_sec(r.first_warning_s)} | {r.evon_verdict or '–'} | {r.cer:.3f} |"
                     + (f" error: {r.error}" if r.error else ""))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def from_dicts(rows: list[dict]) -> list[CallResult]:
    return [CallResult(**row) for row in rows]


def as_dicts(results: list[CallResult]) -> list[dict]:
    return [asdict(r) for r in results]
