"""Voices a synthetic call script (eval/calls/*.yml) with Timbre.

Each turn is spoken by the caller's or receiver's voice and joined with short
pauses into one mono WAV, like a speakerphone recording of both sides.
Timbre output is cached, so re-running costs nothing.

    python scripts/synth_call.py eval/calls/hi_digital_arrest_01.yml
"""

import argparse
import sys
import wave
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kavach.config import CACHE_DIR  # noqa: E402
from kavach.speak.timbre import TimbreClient  # noqa: E402

SAMPLE_RATE = 16000


def synth(script_path: Path, client: TimbreClient, pause_s: float = 0.6) -> Path:
    script = yaml.safe_load(script_path.read_text(encoding="utf-8"))
    language = script["language"]
    voices = script["voices"]
    silence = b"\x00\x00" * int(pause_s * SAMPLE_RATE)
    pcm = bytearray(silence)
    for role, text in script["turns"]:
        audio = client.speak(text, language=language, voice=voices[role], sample_rate=SAMPLE_RATE, speed=1.0)
        pcm += audio.pcm + silence
    out = CACHE_DIR / "calls" / f"{script['id']}.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(bytes(pcm))
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scripts", nargs="+", type=Path)
    args = parser.parse_args()
    client = TimbreClient()
    for path in args.scripts:
        out = synth(path, client)
        seconds = out.stat().st_size / 2 / SAMPLE_RATE
        print(f"{path.name} -> {out} ({seconds:.0f}s)")
    print(f"Timbre API calls made: {client.api_calls}")
