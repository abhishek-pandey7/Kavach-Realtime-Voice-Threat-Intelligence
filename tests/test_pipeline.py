import asyncio
import time

import pytest

from kavach.detect.evon import RedFlag, Verdict
from kavach.detect.keywords import KeywordDetector
from kavach.pipeline import KavachSession, RecordingSpeaker, SessionConfig
from kavach.speak.timbre import Audio
from kavach.stt.prisma import Transcript

SCAM = [
    "नमस्ते, मैं सी बी आई ऑफिस से बोल रहा हूं",
    "आपके नाम पर एक पार्सल में ड्रग्स मिले हैं, आपके खिलाफ अरेस्ट वारंट है",
    "यह बात किसी को मत बताना",
    "वेरिफिकेशन के लिए पैसे ट्रांसफर कीजिए",
]


class FakeTimbre:
    def __init__(self):
        self.spoken = []

    def speak(self, text, language="hi-IN", voice=None, sample_rate=16000, speed=0.95):
        self.spoken.append(text)
        return Audio(b"\x00\x00" * 1600, 16000)  # 0.1 s

    def speak_cloned(self, text, embedding, sample_rate=16000):
        self.spoken.append(f"[cloned] {text}")
        return Audio(b"\x00\x00" * 1600, 16000)


class FakeEvon:
    def __init__(self, verdict):
        self.verdict = verdict
        self.calls = 0

    async def assess(self, lines, language="hi-IN", temperature=0.6):
        self.calls += 1
        await asyncio.sleep(0.01)
        return self.verdict

    async def assess_consistent(self, lines, language="hi-IN", samples=3):
        return Verdict(**{**self.verdict.__dict__, "votes": ["SCAM"] * samples})


class FakeAlerter:
    def __init__(self):
        self.messages = []

    async def send(self, text):
        self.messages.append(text)
        return True


async def transcripts(lines):
    for i, line in enumerate(lines):
        yield Transcript(line, True, f"u{i}", i, 1000, 100, time.monotonic())
        await asyncio.sleep(0.02)


@pytest.fixture(scope="module")
def detector():
    return KeywordDetector()


def run(session, lines):
    return asyncio.run(session.process(transcripts(lines)))


def test_keywords_only_gives_one_soft_warning(detector):
    timbre, events = FakeTimbre(), []
    session = KavachSession(SessionConfig(echo_guard=False), detector, timbre, RecordingSpeaker(),
                            on_event=events.append)
    report = run(session, SCAM)
    assert report["level"] == "SOFT"
    assert len(timbre.spoken) == 1 and "सावधान" in timbre.spoken[0]
    assert report["first_flag_at_s"] is not None
    assert any(e["type"] == "warning" for e in events)


def test_evon_scam_gives_announcement_hard_warning_and_alert(detector):
    timbre, alerter = FakeTimbre(), FakeAlerter()
    verdict = Verdict("SCAM", 95, "digital_arrest", "extraction", [RedFlag("threat", "ड्रग्स")])
    session = KavachSession(SessionConfig(echo_guard=False), detector, timbre, RecordingSpeaker(),
                            evon=FakeEvon(verdict), alerter=alerter)
    report = run(session, SCAM)
    assert report["level"] == "HARD"
    assert any("कवच" in s for s in timbre.spoken)  # announcement
    assert any("गिरफ्तार नहीं करती" in s for s in timbre.spoken)  # digital-arrest template
    assert len(alerter.messages) == 1 and "digital arrest" in alerter.messages[0]


def test_family_voice_used_for_hard_warning(detector):
    timbre = FakeTimbre()
    verdict = Verdict("SCAM", 95, "digital_arrest", "extraction", [RedFlag("threat", "ड्रग्स")])
    config = SessionConfig(echo_guard=False, family_voice={"embedding": "x", "shape": [1, 768], "dtype": "bf16"})
    session = KavachSession(config, detector, timbre, RecordingSpeaker(), evon=FakeEvon(verdict))
    run(session, SCAM)
    assert any(s.startswith("[cloned] माँ, मैं हूँ।") for s in timbre.spoken)


def test_genuine_call_with_evon_safe_stays_quiet(detector):
    timbre = FakeTimbre()
    lines = ["मैं अमेज़न डिलीवरी से बोल रहा हूं", "आपका पार्सल आज आएगा", "दरवाजे पर ओटीपी बता दीजिएगा"]
    session = KavachSession(SessionConfig(echo_guard=False), detector, timbre, RecordingSpeaker(),
                            evon=FakeEvon(Verdict("SAFE", 5)))
    report = run(session, lines)
    assert timbre.spoken == [] and report["level"] in ("NONE", "WATCH")


def test_echo_guard_ignores_kavach_own_voice(detector):
    events = []
    session = KavachSession(SessionConfig(echo_guard=True), detector, FakeTimbre(), RecordingSpeaker(),
                            on_event=events.append)
    session.speaking_until = time.monotonic() + 60
    run(session, ["कोई पैसे या ओटीपी मत दीजिए"])
    assert [e["type"] for e in events if e["type"] != "end"] == ["ignored"]


class CountingEvon(FakeEvon):
    def __init__(self, verdict):
        super().__init__(verdict)
        self.seen, self.consistent_calls = [], 0

    async def assess(self, lines, language="hi-IN", temperature=0.0):
        self.seen.append(list(lines))
        return await super().assess(lines, language, temperature)

    async def assess_consistent(self, lines, language="hi-IN", samples=3):
        self.consistent_calls += 1
        self.seen.append(list(lines))
        return await super().assess_consistent(lines, language, samples)


async def partials(texts):
    for i, text in enumerate(texts):
        yield Transcript(text, False, "u0", i, 500, 0, time.monotonic())
        await asyncio.sleep(0.02)


def test_new_red_flag_in_a_partial_asks_evon_before_the_sentence_ends(detector):
    evon = CountingEvon(Verdict("UNCERTAIN", 40))
    session = KavachSession(SessionConfig(echo_guard=False), detector, FakeTimbre(), RecordingSpeaker(), evon=evon)
    asyncio.run(session.process(partials(["मैं सीबीआई से", "मैं सीबीआई से बोल रहा हूं"])))
    assert evon.seen and evon.seen[0][-1] == "मैं सीबीआई से"  # the partial text was sent
    assert len(evon.seen) == 1  # the second partial added no new category


def test_strong_keywords_skip_straight_to_the_vote(detector):
    evon = CountingEvon(Verdict("SCAM", 95, "digital_arrest", "extraction", [RedFlag("threat", "ड्रग्स")]))
    session = KavachSession(SessionConfig(echo_guard=False), detector, FakeTimbre(), RecordingSpeaker(), evon=evon)
    report = run(session, SCAM)
    assert evon.consistent_calls >= 1
    assert {"first_flag", "evon_confirmed_scam", "warn_hard"} <= set(report["timeline"])
    assert report["timeline"]["first_flag"] <= report["timeline"]["warn_hard"]
