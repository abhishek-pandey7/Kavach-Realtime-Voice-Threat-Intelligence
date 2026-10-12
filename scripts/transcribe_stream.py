"""Live transcription with Gnani Prisma v2.5 from a file or the microphone.

Examples:
    python scripts/transcribe_stream.py --file cache/smoke_hi.wav
    python scripts/transcribe_stream.py --file call.wav --rate 8000
    python scripts/transcribe_stream.py --mic --lang hi-IN
"""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kavach.audio.sources import file_source, mic_source  # noqa: E402
from kavach.config import gnani_api_key  # noqa: E402
from kavach.stt.prisma import PrismaConfig, PrismaStream  # noqa: E402


async def main(args: argparse.Namespace) -> None:
    config = PrismaConfig(language=args.lang, sample_rate=16000, min_silence_ms=args.silence_ms,
                          partials=not args.no_partials)
    stream = PrismaStream(gnani_api_key(), config)
    if args.mic:
        source = mic_source(16000)
        print("Listening on the microphone. Ctrl+C to stop.")
    else:
        via = args.rate if args.rate != 16000 else None
        source = file_source(Path(args.file), 16000, realtime=not args.fast, via_rate=via)
    t0 = time.monotonic()
    async for t in stream.transcribe(source):
        tag = "FINAL  " if t.is_final else "partial"
        print(f"[{t.received_at - t0:6.2f}s] {tag} ({t.audio_duration_ms:.0f} ms audio) {t.text}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="audio file to stream at real-time pace")
    src.add_argument("--mic", action="store_true", help="stream from the default microphone")
    parser.add_argument("--lang", default="hi-IN")
    parser.add_argument("--rate", type=int, default=16000, choices=[8000, 16000],
                        help="8000 simulates telephone bandwidth; audio is still streamed at 16 kHz")
    parser.add_argument("--silence-ms", type=int, default=300)
    parser.add_argument("--no-partials", action="store_true", help="only final transcripts")
    parser.add_argument("--fast", action="store_true", help="don't pace file audio in real time")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        pass
