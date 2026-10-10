# Kavach — Realtime Voice Threat Intelligence

Kavach listens to a phone call in Indian languages, detects scam scripts such as "digital arrest" or fake KYC in real time, and speaks a warning into the call before money moves.

Built for Gnani AI's Great Indian AI Internship Challenge, on Gnani's own models:

- **Prisma v2.5**: streaming speech-to-text
- **Evon v3.3**: reasoning (self-hosted)
- **Timbre v2.5**: text-to-speech and voice cloning

Status: early development. See [PLAN.md](PLAN.md).

## Setup

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows; use .venv/bin/pip on Linux/macOS
echo GNANI_API_KEY=your_key > .env
.venv/Scripts/python scripts/smoke_test.py
```

All test data is synthetic. No real calls, phone numbers or personal data are used.
