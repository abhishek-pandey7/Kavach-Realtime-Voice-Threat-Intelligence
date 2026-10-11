"""Evaluates Kavach on the scripted calls in eval/calls/.

Missing call audio is voiced with Timbre first (cached). Each call is then
streamed through Prisma in real time under every chosen condition.

    python scripts/run_eval.py                                   # phone + phone_snr5
    python scripts/run_eval.py --conditions clean16k,phone,phone_snr10,phone_snr5,phone_snr0
    python scripts/run_eval.py --evon                            # with hosted Evon

Writes eval/REPORT.md and cache/eval/results-<time>.json.
Cost: roughly (call seconds x conditions) of Prisma streaming.
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kavach.config import CACHE_DIR, ROOT, gnani_api_key  # noqa: E402
from kavach.detect.evon import EvonClient  # noqa: E402
from kavach.eval.runner import CONDITIONS, EVAL_DIR, as_dicts, load_script, run_all, write_report  # noqa: E402
from kavach.speak.timbre import TimbreClient  # noqa: E402
from synth_call import synth  # noqa: E402


async def main(args) -> None:
    conditions = args.conditions.split(",")
    unknown = set(conditions) - set(CONDITIONS)
    if unknown:
        sys.exit(f"Unknown condition(s): {unknown}. Choose from {list(CONDITIONS)}")
    timbre = TimbreClient()
    scripts = []
    for path in sorted((ROOT / "eval" / "calls").glob(args.glob)):
        script = load_script(path)
        wav = CACHE_DIR / "calls" / f"{script['id']}.wav"
        if not wav.exists():
            wav = synth(path, timbre)
        scripts.append((script, wav))
    print(f"{len(scripts)} calls x {len(conditions)} conditions, Evon {'on' if args.evon else 'off'}")

    evon = EvonClient() if args.evon else None
    try:
        results = await run_all(scripts, conditions, gnani_api_key(), timbre, evon, args.concurrency)
    finally:
        if evon:
            await evon.close()

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    out = EVAL_DIR / f"results-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps(as_dicts(results), ensure_ascii=False, indent=2), encoding="utf-8")
    report = ROOT / "eval" / "REPORT.md"
    write_report(results, report, evon_used=args.evon)
    print(f"\nResults: {out}\nReport:  {report}")
    print(f"Timbre API calls this run: {timbre.api_calls}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--conditions", default="phone,phone_snr5")
    parser.add_argument("--glob", default="*.yml", help="which scripts in eval/calls/")
    parser.add_argument("--evon", action="store_true")
    parser.add_argument("--concurrency", type=int, default=3)
    asyncio.run(main(parser.parse_args()))
