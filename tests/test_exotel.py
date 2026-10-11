import asyncio
import base64
import json

from kavach.speak.timbre import Audio
from kavach.telephony.exotel import ExotelStream, outbound_chunks, resample_pcm16


def test_outbound_chunks_follow_exotel_rules():
    for rate in (8000, 16000, 24000):
        pcm = b"\x01\x00" * int(rate * 1.37)  # odd length audio
        chunks = outbound_chunks(pcm, rate)
        assert b"".join(chunks).startswith(pcm)
        assert all(3200 <= len(c) <= 100_000 and len(c) % 320 == 0 for c in chunks)
    assert len(outbound_chunks(b"\x00\x00" * 100, 8000)[0]) == 3200  # short tail padded to the minimum


def test_resample_doubles_length():
    pcm = (b"\x10\x00" * 800)
    assert len(resample_pcm16(pcm, 8000, 16000)) == 3200
    assert resample_pcm16(pcm, 16000, 16000) == pcm


class FakeWS:
    def __init__(self, incoming):
        self.incoming = list(incoming)
        self.sent = []

    async def receive_text(self):
        await asyncio.sleep(0)
        return json.dumps(self.incoming.pop(0))

    async def send_text(self, text):
        self.sent.append(json.loads(text))


def test_stream_reads_audio_and_sends_media_with_mark():
    payload = base64.b64encode(b"\x00\x01" * 800).decode()
    ws = FakeWS([
        {"event": "connected"},
        {"event": "start", "stream_sid": "MZ1", "start": {"stream_sid": "MZ1", "call_sid": "CA1",
                                                          "media_format": {"sample_rate": "8000"}}},
        {"event": "media", "media": {"payload": payload}},
        {"event": "stop", "stop": {"reason": "callended"}},
    ])
    stream = ExotelStream(ws, target_rate=16000)

    async def run():
        frames = [f async for f in stream.audio()]
        await stream.speak(Audio(b"\x00\x00" * 8000, 16000), wait=False)
        return frames

    frames = asyncio.run(run())
    assert stream.stream_sid == "MZ1" and stream.sample_rate == 8000
    assert len(frames) == 1 and len(frames[0]) == 3200  # 800 samples at 8 kHz -> 1600 at 16 kHz
    kinds = [m["event"] for m in ws.sent]
    assert kinds[-1] == "mark" and set(kinds[:-1]) == {"media"}
    assert all(m["stream_sid"] == "MZ1" for m in ws.sent)
