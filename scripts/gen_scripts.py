"""Has Evon v3.3 write synthetic call scripts for the evaluation set.

Writes eval/calls/generated/<id>.yml in the same format as the hand-written
scripts, marked `generated: evon-v3.3` and `reviewed: false`. Review them
before trusting results: read each one, fix anything unrealistic, then set
`reviewed: true`.

Caveat: the same model that writes these also judges calls in Kavach, which
can flatter results. Hand-written and human-recorded calls stay the main
test; generated ones add variety, especially genuine look-alikes.

    python scripts/gen_scripts.py --per-scenario 2            # all scenarios
    python scripts/gen_scripts.py --only genuine --per-scenario 3
"""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kavach import config  # noqa: E402,F401  (loads .env)
from kavach.detect.evon import EvonClient  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent.parent / "eval" / "calls" / "generated"

SCAMS = {
    "digital_arrest": "a fake CBI or police officer says the listener's Aadhaar was used in money laundering, "
                      "puts them under 'digital arrest' on a video call, forbids telling family, demands a "
                      "'verification' transfer",
    "courier_customs": "a fake courier or customs officer says a parcel in the listener's name had drugs or fake "
                       "passports, transfers to a fake officer, demands a fine",
    "bank_kyc": "a fake bank employee says KYC expired and the account will be blocked tonight, asks for the OTP "
                "or to install a screen-sharing app",
    "upi_refund": "a caller claims they sent money by mistake and asks the listener to 'approve' a UPI request "
                  "or enter their PIN to send it back",
    "relative_in_trouble": "a caller claims to be a friend of the listener's son or nephew who had an accident or "
                           "was arrested, needs money urgently, says not to call anyone",
    "utility_disconnection": "a fake electricity board officer says power will be cut tonight for an unpaid bill "
                             "and asks for immediate payment to a personal UPI ID",
    "prize_job": "a caller says the listener won a lottery or got a job but must pay a registration or "
                 "processing fee first",
}

GENUINE = {
    "bank_fraud_alert": "a real bank's fraud team asks whether a recent card transaction was the listener's, "
                        "and reminds them never to share an OTP",
    "delivery_otp": "a real delivery agent can't find the address and says to share the delivery OTP at the door",
    "electricity_reminder": "a real electricity office reminds about a pending bill and suggests paying in the "
                            "official app before the due date, no threats",
    "passport_police_verification": "a real police constable schedules the routine passport address "
                                    "verification visit and lists documents to keep ready",
    "insurance_renewal": "an insurance agent reminds that a policy expires next month and offers to send the "
                         "renewal link from the official company website",
    "family_money": "the listener's daughter asks for help paying college fees next week, chats normally",
    "telecom_kyc_store": "a telecom company asks the listener to visit their nearest store with ID for SIM "
                         "re-verification, no payment",
    "job_interview": "an HR person schedules a job interview, says there is no fee of any kind",
}

PROMPT = """Write a realistic phone call script in {language} between a CALLER and a RECEIVER in India.
Scenario: {scenario}.
Rules: 6 to 10 short turns; natural spoken {language} as people really talk on the phone, with
English words where Indians would use them; fictional names only; never include real phone numbers,
account numbers, Aadhaar or UPI IDs (say "this number" or "this account" instead); write numbers as words.
Return JSON: {{"turns": [{{"role": "caller" or "receiver", "text": "..."}}]}}"""

SCHEMA = {
    "type": "object",
    "properties": {"turns": {"type": "array", "minItems": 4, "maxItems": 12, "items": {
        "type": "object",
        "properties": {"role": {"enum": ["caller", "receiver"]}, "text": {"type": "string", "maxLength": 220}},
        "required": ["role", "text"]}}},
    "required": ["turns"],
}

VOICES = {"hi-IN": [("Vikrant", "Urmila"), ("Omkar", "Bhavna"), ("Hemraj", "Ambuja"), ("Roopesh", "Chitra")]}
LANGUAGE_NAMES = {"hi-IN": "Hindi"}


async def write_one(client: EvonClient, scenario: str, description: str, label: str, index: int,
                    language: str) -> Path | None:
    body = {
        "model": client.model, "temperature": 0.8, "top_p": 0.95, "max_tokens": 1200,
        "chat_template_kwargs": {"enable_thinking": False},
        "messages": [{"role": "user", "content": PROMPT.format(language=LANGUAGE_NAMES[language], scenario=description)}],
        "response_format": {"type": "json_schema", "json_schema": {"name": "script", "schema": SCHEMA}},
    }
    resp = await client._http.post(f"{client.base_url}/chat/completions", json=body, timeout=180)
    resp.raise_for_status()
    turns = json.loads(resp.json()["choices"][0]["message"]["content"])["turns"]
    if any(re.search(r"\d{6,}", t["text"]) for t in turns):
        print(f"  skipped {scenario} #{index}: contains a long digit sequence")
        return None
    caller, receiver = VOICES[language][index % len(VOICES[language])]
    script = {
        "id": f"gen_{language[:2]}_{scenario}_{index:02d}",
        "language": language,
        "label": label,
        "scam_type": scenario if label == "scam" else "none",
        "generated": "evon-v3.3",
        "reviewed": False,
        "voices": {"caller": caller, "receiver": receiver},
        "turns": [[t["role"], t["text"].strip()] for t in turns if t["text"].strip()],
    }
    path = OUT_DIR / f"{script['id']}.yml"
    header = "# Generated by Evon v3.3 for evaluation. Fictional. Review before use, then set reviewed: true.\n"
    path.write_text(header + yaml.safe_dump(script, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")
    return path


async def main(args) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    jobs = []
    if args.only in (None, "scam"):
        jobs += [(name, desc, "scam") for name, desc in SCAMS.items()]
    if args.only in (None, "genuine"):
        jobs += [(name, desc, "genuine") for name, desc in GENUINE.items()]
    client = EvonClient(timeout_s=180)
    try:
        for name, desc, label in jobs:
            for i in range(1, args.per_scenario + 1):
                if (OUT_DIR / f"gen_{args.lang[:2]}_{name}_{i:02d}.yml").exists():
                    continue
                try:
                    path = await write_one(client, name, desc, label, i, args.lang)
                    if path:
                        print(f"  wrote {path.name}")
                except Exception as exc:
                    print(f"  failed {name} #{i}: {exc!r}")
    finally:
        await client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--per-scenario", type=int, default=2)
    parser.add_argument("--only", choices=["scam", "genuine"])
    parser.add_argument("--lang", default="hi-IN", choices=list(LANGUAGE_NAMES))
    asyncio.run(main(parser.parse_args()))
