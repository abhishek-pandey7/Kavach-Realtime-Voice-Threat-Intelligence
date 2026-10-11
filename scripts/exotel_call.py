"""Asks Exotel to call a verified number and stream it to Kavach.

Requires the Kavach app running behind a public tunnel (PUBLIC_WSS_BASE) and
EXOTEL_* settings in .env. See docs/EXOTEL_SETUP.md.

    python scripts/exotel_call.py --to +91XXXXXXXXXX --echo   # audio loopback test
    python scripts/exotel_call.py --to +91XXXXXXXXXX          # Kavach on the call
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kavach import config  # noqa: E402,F401  (loads .env)
from kavach.telephony.exotel import place_call  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--to", required=True, help="verified phone number to ring")
    parser.add_argument("--lang", default="hi-IN")
    parser.add_argument("--echo", action="store_true", help="loopback test instead of Kavach")
    args = parser.parse_args()

    base = os.environ.get("PUBLIC_WSS_BASE", "").rstrip("/")
    if not base.startswith("wss://"):
        sys.exit("Set PUBLIC_WSS_BASE=wss://<tunnel host> in .env first.")
    path = "/exotel/echo" if args.echo else "/exotel/ws"
    url = f"{base}{path}?sample-rate=16000&lang={args.lang}"
    print(f"Stream URL: {url}")
    print(json.dumps(asyncio.run(place_call(args.to, url)), indent=2))
