"""Smoke test: Timbre v2.5 speaks a Hindi line, Prisma v2.5 transcribes it back.

Uses one TTS call and one STT call. Output audio goes to cache/.
"""

import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
API_KEY = os.environ["GNANI_API_KEY"]

TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"
STT_URL = "https://api.vachana.ai/stt/v3"

TEXT = "नमस्ते, मैं सीबीआई ऑफिस से बोल रहा हूँ। आपके नाम पर एक पार्सल में ड्रग्स मिले हैं। यह बात किसी को मत बताना।"


def tts(text: str, out: Path) -> None:
    body = {
        "text": text,
        "voice": "Deepak",
        "model": "timbre-v2.5",
        "language": "hi-IN",
        "audio_config": {
            "sample_rate": 16000,
            "num_channels": 1,
            "sample_width": 2,
            "encoding": "linear_pcm",
            "container": "wav",
        },
    }
    t0 = time.perf_counter()
    r = requests.post(TTS_URL, json=body, headers={"X-API-Key-ID": API_KEY}, timeout=60)
    dt = time.perf_counter() - t0
    if r.status_code != 200 or not r.headers.get("content-type", "").startswith("audio"):
        sys.exit(f"TTS failed ({r.status_code}): {r.text[:500]}")
    out.write_bytes(r.content)
    print(f"[Timbre] {len(r.content) / 1024:.0f} KB audio in {dt:.2f}s -> {out}")


def stt(path: Path) -> None:
    t0 = time.perf_counter()
    with path.open("rb") as f:
        r = requests.post(
            STT_URL,
            headers={"X-API-Key-ID": API_KEY},
            files={"audio_file": (path.name, f, "audio/wav")},
            data={"language_code": "hi-IN"},
            timeout=60,
        )
    dt = time.perf_counter() - t0
    if r.status_code != 200:
        sys.exit(f"STT failed ({r.status_code}): {r.text[:500]}")
    data = r.json()
    print(f"[Prisma] {dt:.2f}s, response: {data}")


if __name__ == "__main__":
    out = ROOT / "cache" / "smoke_hi.wav"
    out.parent.mkdir(exist_ok=True)
    tts(TEXT, out)
    stt(out)
