"""Runs Kavach end to end on a recorded call or the live microphone.

    python scripts/run_kavach.py --file cache/calls/hi_digital_arrest_01.wav
    python scripts/run_kavach.py --file call.wav --rate 8000 --evon
    python scripts/run_kavach.py --mic --speaker local --evon     # Guardian mode

Evon is used only with --evon (needs EVON_BASE_URL). Warnings are recorded,
not played, unless --speaker local. A JSON report goes to cache/reports/.
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kavach.alerts.telegram import TelegramAlerter  # noqa: E402
from kavach.audio.sources import file_source, mic_source  # noqa: E402
from kavach.config import CACHE_DIR, gnani_api_key  # noqa: E402
from kavach.detect.evon import EvonClient  # noqa: E402
from kavach.detect.keywords import KeywordDetector  # noqa: E402
from kavach.pipeline import KavachSession, RecordingSpeaker, SessionConfig  # noqa: E402
from kavach.speak.player import play  # noqa: E402
from kavach.speak.timbre import TimbreClient, load_voice  # noqa: E402
from kavach.stt.prisma import PrismaConfig, PrismaStream  # noqa: E402

COLORS = {"NONE": "", "WATCH": "\033[33m", "SOFT": "\033[35m", "HARD": "\033[31m"}
RESET = "\033[0m"


def print_event(e: dict) -> None:
    t = f"[{e['t']:6.2f}s]"
    kind = e["type"]
    if kind == "transcript" and e["final"]:
        flags = ", ".join(f"{f['category']}:{f['phrase']}" for f in e["flags"])
        print(f"{t} 🗣  {e['text']}" + (f"\n          ⚑ {flags}" if flags else ""))
    elif kind == "risk":
        if e["level"] != getattr(print_event, "last_level", None) or e["risk"] != getattr(print_event, "last_risk", None):
            bar = "█" * (e["risk"] // 5)
            print(f"{t} {COLORS[e['level']]}risk {e['risk']:3d} {bar:<20} {e['level']}{RESET}"
                  f"  stages={'→'.join(e['stages'])}  evon={e['evon_verdict']}")
            print_event.last_level, print_event.last_risk = e["level"], e["risk"]
    elif kind == "verdict":
        print(f"{t} 🧠 Evon: {e['verdict']} risk={e['risk']} type={e['scam_type']} "
              f"({e['latency_s']}s){' votes=' + str(e['votes']) if e['votes'] else ''}"
              f"{' error=' + e['error'] if e['error'] else ''}")
    elif kind == "warning":
        print(f"{t} 🔊 {e['level']} warning (+{e['after_trigger_s']}s after trigger): {e['text']}")
    elif kind == "alert":
        print(f"{t} 📲 family alert {'sent' if e['sent'] else 'logged (Telegram not set up)'}")
    elif kind == "ignored":
        print(f"{t} (ignored while Kavach speaks: {e['text']})")


async def main(args: argparse.Namespace) -> None:
    prisma = PrismaStream(gnani_api_key(), PrismaConfig(language=args.lang, sample_rate=args.rate))
    if args.mic:
        source = mic_source(args.rate)
        print("Listening. Put the call on speaker. Ctrl+C to stop.\n")
    else:
        source = file_source(Path(args.file), args.rate)

    speaker = play if args.speaker == "local" else RecordingSpeaker()
    evon = EvonClient() if args.evon else None
    family = load_voice(args.family_voice) if args.family_voice else None
    config = SessionConfig(language=args.lang, echo_guard=args.mic,
                           speak_sample_rate=16000, family_voice=family)
    session = KavachSession(config, KeywordDetector(), TimbreClient(), speaker, evon=evon,
                            alerter=TelegramAlerter(), on_event=print_event)
    try:
        report = await session.process(prisma.transcribe(source))
    finally:
        if evon:
            await evon.close()

    out = CACHE_DIR / "reports" / f"{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nPeak risk {report['peak_risk']}, level {report['level']}, "
          f"{len(report['warnings'])} warning(s). Report: {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--file")
    src.add_argument("--mic", action="store_true")
    parser.add_argument("--lang", default="hi-IN")
    parser.add_argument("--rate", type=int, default=16000, choices=[8000, 16000])
    parser.add_argument("--evon", action="store_true", help="use the hosted Evon (EVON_BASE_URL)")
    parser.add_argument("--speaker", choices=["record", "local"], default="record")
    parser.add_argument("--family-voice", help="name of a cloned voice in cache/voices/")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        pass
