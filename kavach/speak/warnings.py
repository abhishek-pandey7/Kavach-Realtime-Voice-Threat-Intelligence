"""What Kavach says, in each language.

Warnings name the specific trick ("police never arrest over the phone")
rather than just saying "fraud", following scam-psychology research
(docs/RESEARCH.md, Stajano and Wilson). Numbers are written as words, as
Timbre's docs recommend.

Hindi and English are reviewed. Tamil and Bengali are drafts that need a
native speaker's review before they are used in a demo.
"""

from kavach.detect.scorer import Level

# Spoken to everyone on the call at the first HARD warning.
ANNOUNCE = {
    "hi-IN": "यह कॉल कवच द्वारा सुरक्षा के लिए सुनी जा रही है।",
    "en-IN": "This call is being monitored by Kavach for your safety.",
    "ta-IN": "இந்த அழைப்பு கவச் மூலம் பாதுகாப்புக்காகக் கண்காணிக்கப்படுகிறது.",
    "bn-IN": "এই কলটি নিরাপত্তার জন্য কবচ দ্বারা শোনা হচ্ছে।",
}

SOFT = {
    "hi-IN": "सावधान रहिए। यह कॉल धोखा हो सकती है। कोई पैसे, ओटीपी या जानकारी मत दीजिए।",
    "en-IN": "Be careful. This call may be a scam. Do not share money, OTPs or personal details.",
    "ta-IN": "கவனமாக இருங்கள். இது மோசடி அழைப்பாக இருக்கலாம். பணம், ஓடிபி அல்லது தகவல் எதையும் கொடுக்காதீர்கள்.",
    "bn-IN": "সাবধান। এটি প্রতারণার কল হতে পারে। টাকা, ওটিপি বা কোনো তথ্য দেবেন না।",
}

HARD_GENERIC = {
    "hi-IN": "रुकिए। यह कॉल धोखा है। कोई पैसे या ओटीपी मत दीजिए। फोन काट दीजिए और परिवार को बताइए।",
    "en-IN": "Stop. This call is a scam. Do not send money or share any OTP. Hang up and tell your family.",
    "ta-IN": "நிறுத்துங்கள். இது மோசடி அழைப்பு. பணமோ ஓடிபியோ கொடுக்காதீர்கள். அழைப்பைத் துண்டித்து குடும்பத்தினரிடம் சொல்லுங்கள்.",
    "bn-IN": "থামুন। এটি প্রতারণার কল। টাকা বা ওটিপি দেবেন না। ফোন কেটে পরিবারকে জানান।",
}

# The specific trick, per scam type (Hindi and English).
HARD_BY_TYPE = {
    "digital_arrest": {
        "hi-IN": "पुलिस या सीबीआई कभी फोन या वीडियो कॉल पर गिरफ्तार नहीं करती। यह धोखा है, कॉल काट दीजिए।",
        "en-IN": "Police and the CBI never arrest anyone over a phone or video call. This is a scam. Hang up.",
    },
    "courier_customs": {
        "hi-IN": "कोई कूरियर कंपनी या कस्टम अधिकारी फोन पर पैसे नहीं मांगता। यह धोखा है, कॉल काट दीजिए।",
        "en-IN": "No courier company or customs officer asks for money over the phone. This is a scam. Hang up.",
    },
    "bank_kyc": {
        "hi-IN": "बैंक कभी ओटीपी, पिन या सीवीवी नहीं मांगता। कुछ मत बताइए, कॉल काट दीजिए।",
        "en-IN": "Your bank will never ask for an OTP, PIN or CVV. Don't share anything. Hang up.",
    },
    "upi_refund": {
        "hi-IN": "पैसे लेने के लिए कभी पिन नहीं डालना पड़ता। यह धोखा है, कुछ मत कीजिए।",
        "en-IN": "You never need to enter a PIN to receive money. This is a scam.",
    },
    "relative_in_trouble": {
        "hi-IN": "पहले अपने रिश्तेदार को खुद फोन करके पक्का कीजिए। अभी कोई पैसे मत भेजिए।",
        "en-IN": "First call your relative yourself to check. Do not send any money now.",
    },
    "utility_disconnection": {
        "hi-IN": "बिजली विभाग ऐसे फोन करके पैसे नहीं मांगता। कॉल काट दीजिए।",
        "en-IN": "The electricity board does not demand payment through calls like this. Hang up.",
    },
    "prize_job": {
        "hi-IN": "इनाम या नौकरी के लिए फीस मांगना धोखा है। कोई पैसे मत भेजिए।",
        "en-IN": "Asking for a fee for a prize or a job is a scam. Do not send any money.",
    },
}

# Said first when the warning plays in a family member's cloned voice.
FAMILY_OPENER = {
    "hi-IN": "माँ, मैं हूँ।",
    "en-IN": "Mom, it's me.",
}


def _pick(table: dict, language: str) -> str:
    return table.get(language) or table.get("hi-IN") or next(iter(table.values()))


def warning_text(level: Level, language: str = "hi-IN", scam_type: str = "none",
                 evon_warning: str = "") -> str:
    """The sentence to speak for a level. Evon's own warning is used for HARD
    when present; otherwise a reviewed template."""
    if level == Level.SOFT:
        return _pick(SOFT, language)
    if evon_warning.strip():
        return evon_warning.strip()
    by_type = HARD_BY_TYPE.get(scam_type)
    if by_type and language in by_type:
        return by_type[language]
    return _pick(HARD_GENERIC, language)


def all_templates() -> list[tuple[str, str]]:
    """(language, text) for every fixed sentence, for pre-generating audio."""
    out = []
    for table in (ANNOUNCE, SOFT, HARD_GENERIC):
        out.extend(table.items())
    for by_lang in HARD_BY_TYPE.values():
        out.extend(by_lang.items())
    return out
