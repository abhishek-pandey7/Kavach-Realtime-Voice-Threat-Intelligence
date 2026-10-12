import io
import json
import wave

import httpx

from kavach.detect.scorer import Level
from kavach.speak.timbre import Audio, TimbreClient
from kavach.speak.warnings import HARD_BY_TYPE, SOFT, all_templates, warning_text


def _wav(seconds=0.5, rate=16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(seconds * rate))
    return buf.getvalue()


def test_warning_text_selection():
    assert warning_text(Level.SOFT, "hi-IN") == SOFT["hi-IN"]
    assert warning_text(Level.HARD, "hi-IN", "digital_arrest") == HARD_BY_TYPE["digital_arrest"]["hi-IN"]
    assert warning_text(Level.HARD, "hi-IN", "digital_arrest", evon_warning=" कॉल काटिए ") == "कॉल काटिए"
    # Unknown language falls back to Hindi; known language without a typed template uses generic.
    assert warning_text(Level.SOFT, "xx-IN") == SOFT["hi-IN"]
    assert "ஓடிபி" in warning_text(Level.HARD, "ta-IN", "digital_arrest")


def test_templates_have_no_digits():
    # Timbre reads digits unreliably; templates spell numbers out.
    assert all(not any(ch.isdigit() for ch in text) for _, text in all_templates())


def test_timbre_cache_avoids_repeat_calls(tmp_path):
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(200, content=_wav(), headers={"content-type": "audio/wav"})

    client = TimbreClient(api_key="k", cache_dir=tmp_path, transport=httpx.MockTransport(handler))
    a = client.speak("नमस्ते", "hi-IN")
    b = client.speak("नमस्ते", "hi-IN")
    assert client.api_calls == 1 and len(requests) == 1
    assert requests[0]["voice"] == "Nalini" and requests[0]["model"] == "timbre-v2.5"
    assert isinstance(a, Audio) and a.pcm == b.pcm and abs(a.duration_s - 0.5) < 0.01
