"""Settings loaded from the environment (.env at the repo root)."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

CACHE_DIR = ROOT / "cache"


def require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set. Add it to {ROOT / '.env'}")
    return value


def gnani_api_key() -> str:
    return require("GNANI_API_KEY")
