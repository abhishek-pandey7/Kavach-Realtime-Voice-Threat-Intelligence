"""Replays every scripted call turn by turn through Kavach's detector and
scorer, without audio. Costs no Gnani credits; with --evon it uses the hosted
Evon (Kaggle GPU time only).

Compares keywords alone against keywords + Evon, using the same RiskScorer
rules as the live pipeline (a SCAM verdict must survive a majority vote).

    python scripts/text_eval.py            # keywords only
    python scripts/text_eval.py --evon     # both, side by side
"""

import argparse
import asyncio
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kavach import config  # noqa: E402,F401  (loads .env)
from kavach.detect.evon import EvonClient  # noqa: E402
from kavach.detect.keywords import KeywordDetector  # noqa: E402
from kavach.detect.scorer import Level, RiskScorer  # noqa: E402

CALLS = Path(__file__).resolve().parent.parent / "eval" / "calls"


async def replay(script: dict, detector: KeywordDetector, evon: EvonClient | None) -> dict:
    scorer = RiskScorer()
    lines = [text for _, text in script["turns"]]
    first_warn = first_hard = None
    for n, line in enumerate(lines, 1):
        scorer.add_hits(detector.scan(line))
        if evon is not None:
            v = await evon.assess(lines[:n], script["language"])
            if v.verdict == "SCAM":
                v = await evon.assess_consistent(lines[:n], script["language"], samples=3)
            scorer.add_verdict(v)
        state = scorer.evaluate(now=n * 10.0)
        if state.level >= Level.SOFT and first_warn is None:
            first_warn = n
        if state.level == Level.HARD and first_hard is None:
            first_hard = n
    return {"level": scorer.level.name, "first_warn": first_warn, "first_hard": first_hard,
            "turns": len(lines), "evon": scorer.verdict.verdict if scorer.verdict else None}


def mark(label: str, level: str) -> str:
    warned = level in ("SOFT", "HARD")
    return "✓" if warned == (label == "scam") else "✗"


async def main(use_evon: bool) -> None:
    detector = KeywordDetector()
    evon = EvonClient(timeout_s=30) if use_evon else None
    scripts = [yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted(CALLS.glob("*.yml"))]
    totals = {"kw": [0, 0], "evon": [0, 0]}  # correct, total
    print(f"{'call':<36}{'label':<9}{'keywords only':<22}{'keywords + Evon' if use_evon else ''}")
    try:
        for s in scripts:
            kw = await replay(s, detector, None)
            totals["kw"][0] += mark(s["label"], kw["level"]) == "✓"
            totals["kw"][1] += 1
            row = f"{s['id']:<36}{s['label']:<9}{mark(s['label'], kw['level'])} {kw['level']:<6}" \
                  f"{('turn ' + str(kw['first_warn'])) if kw['first_warn'] else '':<13}"
            if evon:
                ev = await replay(s, detector, evon)
                totals["evon"][0] += mark(s["label"], ev["level"]) == "✓"
                totals["evon"][1] += 1
                row += f"{mark(s['label'], ev['level'])} {ev['level']:<6}" \
                       f"{('warn turn ' + str(ev['first_warn'])) if ev['first_warn'] else '':<13}" \
                       f"{('HARD turn ' + str(ev['first_hard'])) if ev['first_hard'] else ''}"
            print(row, flush=True)
    finally:
        if evon:
            await evon.close()
    print(f"\nKeywords only: {totals['kw'][0]}/{totals['kw'][1]} correct")
    if use_evon:
        print(f"Keywords + Evon: {totals['evon'][0]}/{totals['evon'][1]} correct")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--evon", action="store_true")
    asyncio.run(main(parser.parse_args().evon))
