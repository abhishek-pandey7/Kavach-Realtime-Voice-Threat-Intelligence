"""After a flagged call: a plain-language debrief and a complaint draft.

The debrief tells the person what just happened and what to do next, in
their language. The complaint draft is a starting point for India's
cybercrime helpline (1930) or cybercrime.gov.in: it lists what the caller
claimed and asked for, quoting the call, with OTPs, account and ID numbers
still masked. Nothing is filed automatically.

Built from fixed templates, so it works without Evon and costs nothing.
"""

from datetime import datetime

SCAM_NAMES = {
    "digital_arrest": ("डिजिटल अरेस्ट (नकली पुलिस/सीबीआई)", "fake police/CBI 'digital arrest'"),
    "courier_customs": ("कूरियर/कस्टम पार्सल", "courier/customs parcel"),
    "bank_kyc": ("बैंक/केवाईसी", "bank/KYC"),
    "upi_refund": ("यूपीआई रिफंड", "UPI refund"),
    "relative_in_trouble": ("रिश्तेदार मुसीबत में", "relative in trouble"),
    "utility_disconnection": ("बिजली/कनेक्शन कटने", "electricity/utility disconnection"),
    "prize_job": ("इनाम/नौकरी/लॉटरी", "prize, job or lottery"),
    "other": ("धोखाधड़ी", "fraud"),
    "none": ("संदिग्ध", "suspicious"),
}

FLAG_NAMES = {
    "fake_authority": ("खुद को अधिकारी या बैंक वाला बताया", "claimed to be an official or bank employee"),
    "threat": ("गिरफ्तारी, केस या खाता बंद होने की धमकी दी", "threatened arrest, a case or account closure"),
    "urgency": ("तुरंत करने का दबाव डाला", "pressured to act immediately"),
    "secrecy": ("किसी को न बताने को कहा", "told the listener not to tell anyone"),
    "payment_demand": ("पैसे भेजने या फीस भरने को कहा", "asked for money, a fee or a transfer"),
    "credential_request": ("ओटीपी, पिन या कार्ड की जानकारी मांगी", "asked for an OTP, PIN or card details"),
    "remote_access": ("कोई ऐप डाउनलोड करने या लिंक खोलने को कहा", "asked to install an app or open a link"),
    "hook": ("पार्सल, केवाईसी या रिफंड का बहाना बनाया", "used a parcel, KYC or refund pretext"),
    "too_good": ("इनाम या कमाई का लालच दिया", "offered a prize or easy earnings"),
}

NEXT_STEPS = {
    "hi-IN": [
        "अगर पैसे भेज दिए हैं, तो तुरंत 1930 पर कॉल करें। जितनी जल्दी, पैसे वापस मिलने की उतनी उम्मीद।",
        "अपने बैंक को फोन करके खाता या कार्ड रुकवाएं।",
        "cybercrime.gov.in पर शिकायत दर्ज करें।",
        "किसी को भी ओटीपी, पिन या पासवर्ड न बताएं। असली पुलिस या बैंक कभी नहीं मांगते।",
    ],
    "en-IN": [
        "If any money was sent, call 1930 immediately. The sooner you report, the better the chance of recovery.",
        "Call your bank to block the account or card.",
        "File a complaint at cybercrime.gov.in.",
        "Never share an OTP, PIN or password. Real police and banks never ask for them.",
    ],
}


def _lang(language: str) -> int:
    return 0 if language == "hi-IN" else 1


def build_debrief(report: dict, language: str = "hi-IN", when: datetime | None = None) -> dict | None:
    """Returns the debrief for a session report, or None if the call wasn't flagged."""
    if report.get("level") not in ("SOFT", "HARD"):
        return None
    i = _lang(language)
    evon = report.get("evon") or {}
    scam_type = evon.get("scam_type") if evon.get("verdict") == "SCAM" else "none"
    scam_name = SCAM_NAMES.get(scam_type or "none", SCAM_NAMES["other"])[i]

    # Red flags: Evon's quoted evidence when it confirmed a scam, else the keyword categories.
    quoted = [(f["category"], f["evidence"]) for f in evon.get("flags", [])] if evon.get("verdict") == "SCAM" else []
    categories = list(dict.fromkeys([c for c, _ in quoted] + list(report.get("categories", []))))
    categories = [c for c in categories if c in FLAG_NAMES]
    flag_lines = [FLAG_NAMES[c][i] for c in categories]

    if i == 0:
        summary = f"यह कॉल {scam_name} धोखाधड़ी जैसी लग रही थी। कॉल करने वाले ने: " + "; ".join(flag_lines) + "।"
    else:
        summary = f"This call looked like a {scam_name} scam. The caller " + "; ".join(flag_lines) + "."

    when = when or datetime.now()
    complaint = _complaint(report, scam_type or "none", quoted, categories, when)
    return {
        "summary": summary,
        "next_steps": NEXT_STEPS.get(language, NEXT_STEPS["en-IN"]),
        "complaint_draft": complaint,
        "scam_type": scam_type,
    }


def _complaint(report: dict, scam_type: str, quoted: list[tuple[str, str]], categories: list[str],
               when: datetime) -> str:
    """English draft for 1930 / cybercrime.gov.in (portal forms are in English)."""
    lines = [
        "Complaint draft (review and edit before submitting; Kavach has not filed anything)",
        "",
        f"Date and time of call: {when.strftime('%d %b %Y, %I:%M %p')}",
        "Caller's phone number: <fill in from your call log>",
        f"Type of fraud suspected: {SCAM_NAMES.get(scam_type, SCAM_NAMES['other'])[1]}",
        f"Call duration observed by Kavach: about {int(report.get('duration_s', 0))} seconds",
        "",
        "What the caller did:",
    ]
    lines += [f"- {FLAG_NAMES[c][1]}" for c in categories]
    if quoted:
        lines += ["", "Words used by the caller (from Kavach's transcript; numbers masked):"]
        lines += [f'- "{evidence}"' for _, evidence in quoted[:5]]
    lines += [
        "",
        "Money lost: <amount, if any, with UPI / bank transaction reference>",
        "Action taken: call ended after Kavach's warning; family informed.",
    ]
    return "\n".join(lines)
