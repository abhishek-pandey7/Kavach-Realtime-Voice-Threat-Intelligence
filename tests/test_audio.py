from kavach.audio.sources import Rechunker
from kavach.stt.prisma import PrismaConfig


def test_rechunker_splits_into_exact_frames():
    r = Rechunker(4)
    assert r.push(b"abcdef") == [b"abcd"]
    assert r.push(b"gh") == [b"efgh"]
    assert r.push(b"i") == []
    assert r.flush() == b"i\x00\x00\x00"
    assert r.flush() is None


def test_prisma_headers_include_required_fields():
    h = PrismaConfig(language="ta-IN", sample_rate=8000).headers("key")
    assert h["x-api-key-id"] == "key"
    assert h["lang_code"] == "ta-IN"
    assert h["x-sample-rate"] == "8000"


def test_prisma_rejects_unknown_language():
    try:
        PrismaConfig(language="xx-IN").headers("key")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_parse_partial_and_final_events():
    from kavach.stt.prisma import _parse_transcript

    partial = _parse_transcript({"type": "partial_transcript", "utterance_id": "u1", "seq": 3,
                                 "stable_text": "aapke naam", "volatile_text": "par", "audio_ms": 900})
    assert not partial.is_final and partial.text == "aapke naam par" and partial.utterance_id == "u1"
    final = _parse_transcript({"type": "final_transcript", "utterance_id": "u1", "segment_index": 1,
                               "output": {"literal": "aapke naam par parcel"}, "latency": 120})
    assert final.is_final and final.text == "aapke naam par parcel" and final.latency_ms == 120
