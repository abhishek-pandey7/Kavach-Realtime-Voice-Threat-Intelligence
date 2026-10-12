"""Pre-generates every fixed warning with Timbre so calls replay from cache.

Each sentence costs one Timbre call the first time and nothing afterwards.
    python scripts/prebuild_warnings.py --lang hi-IN          # Hindi only
    python scripts/prebuild_warnings.py --lang all --rate 8000 # telephone audio
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kavach.speak.timbre import TimbreClient  # noqa: E402
from kavach.speak.warnings import all_templates  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lang", default="hi-IN", help="language code or 'all'")
    parser.add_argument("--rate", type=int, default=16000, choices=[8000, 16000, 24000])
    args = parser.parse_args()

    client = TimbreClient()
    for language, text in all_templates():
        if args.lang != "all" and language != args.lang:
            continue
        audio = client.speak(text, language=language, sample_rate=args.rate)
        print(f"{language} {audio.duration_s:4.1f}s  {text}")
    print(f"\nTimbre API calls made: {client.api_calls} (the rest came from cache/tts)")
