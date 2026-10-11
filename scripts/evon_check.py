"""Checks a hosted Evon v3.3 endpoint: latency and verdicts on sample calls.

Set EVON_BASE_URL (and EVON_API_KEY if the server needs one) in .env, then:
    python scripts/evon_check.py
    python scripts/evon_check.py --samples 3   # also test the majority vote
    python scripts/evon_check.py --calls       # score eval/calls scripts turn by turn
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kavach import config  # noqa: E402,F401  (loads .env)
from kavach.detect.evon import EvonClient  # noqa: E402

CASES = {
    "digital arrest (scam)": [
        "नमस्ते, मैं सी बी आई ऑफिस से बोल रहा हूं",
        "आपके नाम पर एक पार्सल में ड्रग्स मिले हैं, आपके खिलाफ अरेस्ट वारंट है",
        "यह बात किसी को मत बताना, वीडियो कॉल पर बने रहिए",
        "वेरिफिकेशन के लिए पचास हजार रुपये इस अकाउंट में ट्रांसफर कीजिए",
    ],
    "delivery with OTP (genuine)": [
        "हेलो, मैं अमेज़न डिलीवरी से बोल रहा हूं",
        "आपका पार्सल आज शाम को आएगा, घर पर कोई होगा?",
        "डिलीवरी के समय जो ओटीपी आएगा वो दरवाजे पर बता दीजिएगा",
    ],
    "bank fraud alert (genuine)": [
        "Good afternoon, this is the fraud monitoring team from your bank",
        "We noticed a transaction of 2000 rupees at an online store, was this you?",
        "Please note, we will never ask for your OTP or PIN. If it wasn't you, reply NO to our SMS",
    ],
}


async def scripted(client: EvonClient) -> None:
    """Feeds each eval/calls script to Evon turn by turn, like a live call, and scores it."""
    import statistics

    import yaml

    rows, latencies = [], []
    for path in sorted((Path(__file__).resolve().parent.parent / "eval" / "calls").glob("*.yml")):
        script = yaml.safe_load(path.read_text(encoding="utf-8"))
        lines = [text for _, text in script["turns"]]
        first_scam_turn, final = None, None
        for n in range(1, len(lines) + 1):
            t0 = time.perf_counter()
            v = await client.assess(lines[:n], script["language"])
            if v.verdict == "SCAM":  # as in the pipeline: SCAM must survive a majority vote
                v = await client.assess_consistent(lines[:n], script["language"], samples=3)
            latencies.append(time.perf_counter() - t0)
            if v.error is None:  # the pipeline keeps the last good verdict
                final = v
            if v.verdict == "SCAM" and first_scam_turn is None:
                first_scam_turn = n
        final = final or v
        correct = (final.verdict == "SCAM") == (script["label"] == "scam")
        rows.append(correct)
        print(f"{'✓' if correct else '✗'} {script['id']:<26} label={script['label']:<7} final={final.verdict:<9} "
              f"type={final.scam_type:<20} first SCAM at turn {first_scam_turn or '-'}/{len(lines)}"
              f"{'  error=' + final.error if final.error else ''}")
    print(f"\n{sum(rows)}/{len(rows)} correct. Latency per call: median {statistics.median(latencies):.2f}s, "
          f"max {max(latencies):.2f}s over {len(latencies)} requests")


async def main(samples: int, calls: bool) -> None:
    client = EvonClient(timeout_s=30)
    print(f"Endpoint: {client.base_url}  model: {client.model}\n")
    if calls:
        try:
            await scripted(client)
        finally:
            await client.close()
        return
    try:
        for name, lines in CASES.items():
            t0 = time.perf_counter()
            if samples > 1:
                v = await client.assess_consistent(lines, samples=samples)
            else:
                v = await client.assess(lines)
            dt = time.perf_counter() - t0
            print(f"== {name}: {v.verdict} risk={v.risk} type={v.scam_type} stage={v.stage} ({dt:.2f}s)")
            if v.error:
                print(f"   error: {v.error}")
            for f in v.red_flags:
                print(f"   - {f.category}: {f.evidence}")
            if v.dropped_flags:
                print(f"   ({v.dropped_flags} flag(s) dropped: evidence not in transcript)")
            if v.votes:
                print(f"   votes: {v.votes}")
            if v.warning:
                print(f"   warning: {v.warning}")
            print()
    finally:
        await client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--calls", action="store_true", help="score the scripted calls in eval/calls turn by turn")
    args = parser.parse_args()
    asyncio.run(main(args.samples, args.calls))
