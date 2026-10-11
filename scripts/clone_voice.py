"""Creates a cloned voice for family warnings, from a consented recording.

Record 10 to 30 seconds of the family member reading any text calmly, in a
quiet room. Only clone the voice of someone who has agreed to it. The
embedding is stored locally in cache/voices/ (not committed).

    python scripts/clone_voice.py --name son --audio recordings/son.wav --consent
    python scripts/clone_voice.py --name son --say "माँ, मैं हूँ। यह कॉल धोखा है।"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kavach.config import CACHE_DIR  # noqa: E402
from kavach.speak.timbre import TimbreClient, load_voice, save_voice  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", required=True, help="short name for the voice, e.g. son")
    parser.add_argument("--audio", help="reference recording (5 to 30 s)")
    parser.add_argument("--consent", action="store_true", help="confirm the speaker agreed to cloning")
    parser.add_argument("--say", help="test sentence to synthesise in the cloned voice")
    args = parser.parse_args()

    client = TimbreClient()
    if args.audio:
        if not args.consent:
            sys.exit("Refusing to clone without --consent. Only clone a voice whose owner agreed.")
        path = save_voice(args.name, client.clone(Path(args.audio)))
        print(f"Saved voice embedding to {path}")
    if args.say:
        embedding = load_voice(args.name)
        if embedding is None:
            sys.exit(f"No voice named {args.name!r}. Create it with --audio first.")
        audio = client.speak_cloned(args.say, embedding)
        out = CACHE_DIR / f"cloned_{args.name}_sample.wav"
        import wave
        with wave.open(str(out), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(audio.sample_rate)
            w.writeframes(audio.pcm)
        print(f"Wrote {audio.duration_s:.1f}s sample to {out}")
