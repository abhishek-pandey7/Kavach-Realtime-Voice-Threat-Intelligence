import asyncio
import json

import httpx

from kavach.detect.evon import EvonClient, Verdict, extract_json, majority, parse_verdict

LINES = [
    "नमस्ते, मैं सी बी आई ऑफिस से बोल रहा हूँ",
    "आपके नाम पर एक पार्सल में ड्रग्स मिले हैं",
    "यह बात किसी को मत बताना",
]

SCAM_REPLY = {
    "verdict": "SCAM", "risk": 88, "scam_type": "digital_arrest", "stage": "isolation",
    "red_flags": [
        {"category": "fake_authority", "evidence": "सी बी आई ऑफिस से बोल रहा"},
        {"category": "threat", "evidence": "पार्सल में ड्रग्स मिले हैं"},
        {"category": "secrecy", "evidence": "किसी को मत बताना"},
        {"category": "payment_demand", "evidence": "पैसे ट्रांसफर करो"},  # not in transcript
    ],
    "warning": "सावधान, पुलिस फोन पर गिरफ्तार नहीं करती। कॉल काट दीजिए।",
}


def test_extract_json_handles_think_blocks_and_fences():
    reply = "<think>hmm</think>\n```json\n{\"verdict\": \"SAFE\", \"risk\": 3}\n```"
    assert extract_json(reply) == {"verdict": "SAFE", "risk": 3}


def test_evidence_guard_drops_hallucinated_flags():
    v = parse_verdict(SCAM_REPLY, LINES)
    assert v.verdict == "SCAM" and v.risk == 88
    assert [f.category for f in v.red_flags] == ["fake_authority", "threat", "secrecy"]
    assert v.dropped_flags == 1


def test_scam_without_supported_evidence_becomes_uncertain():
    obj = {"verdict": "SCAM", "risk": 95, "red_flags": [{"category": "threat", "evidence": "invented words"}]}
    v = parse_verdict(obj, LINES)
    assert v.verdict == "UNCERTAIN" and v.risk <= 60 and v.warning == ""


def test_invalid_fields_are_clamped():
    v = parse_verdict({"verdict": "maybe", "risk": 250, "scam_type": "x", "stage": "y"}, LINES)
    assert (v.verdict, v.risk, v.stage) == ("UNCERTAIN", 100, "none")


def test_majority_vote():
    votes = [Verdict("SCAM", 80), Verdict("SCAM", 90), Verdict("SAFE", 10)]
    m = majority(votes)
    assert m.verdict == "SCAM" and m.risk == 80 and m.votes == ["SCAM", "SCAM", "SAFE"]
    split = majority([Verdict("SCAM", 80), Verdict("SAFE", 10), Verdict("UNCERTAIN", 50)])
    assert split.verdict == "UNCERTAIN"


def _client(handler):
    return EvonClient(base_url="http://evon.test/v1", model="model", transport=httpx.MockTransport(handler))


def test_client_sends_openai_request_and_parses_reply():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        content = json.dumps(SCAM_REPLY, ensure_ascii=False)
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    async def run():
        client = _client(handler)
        try:
            return await client.assess(LINES, "hi-IN")
        finally:
            await client.close()

    v = asyncio.run(run())
    assert v.verdict == "SCAM"
    assert seen["chat_template_kwargs"] == {"enable_thinking": False}
    schema = seen["response_format"]["json_schema"]["schema"]
    assert schema["properties"]["flags"]["items"]["properties"]["evidence"]["maxLength"] == 60
    assert "Hindi" in seen["messages"][-1]["content"]


def test_client_retries_without_json_mode_and_survives_errors():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append(body.get("response_format", {}).get("type"))
        if "response_format" in body:
            return httpx.Response(400, json={"error": "unsupported"})
        return httpx.Response(200, json={"choices": [{"message": {"content": "not json"}}]})

    async def run():
        client = _client(handler)
        try:
            return await client.assess(LINES)
        finally:
            await client.close()

    v = asyncio.run(run())
    assert calls == ["json_schema", "json_object", None]
    assert v.error is not None and v.verdict == "UNCERTAIN"


def test_compact_flag_pairs_are_parsed():
    obj = {"verdict": "SCAM", "risk": 90, "flags": [["threat", "पार्सल में ड्रग्स मिले हैं"], ["secrecy", "किसी को मत बताना"]]}
    v = parse_verdict(obj, LINES)
    assert [f.category for f in v.red_flags] == ["threat", "secrecy"]


def test_few_shot_examples_are_sent_before_the_transcript():
    from kavach.detect.evon import build_messages

    roles = [m["role"] for m in build_messages(LINES, "hi-IN")]
    assert roles == ["system", "user", "assistant", "user", "assistant", "user"]


def test_evidence_guard_tolerates_small_copy_errors_but_not_inventions():
    from kavach.detect.evon import _evidence_supported
    from kavach.detect.normalize import normalize

    transcript = normalize("वेरिफिकेशन के लिए पचास हजार रुपये इस अकाउंट में ट्रांसफर कीजिए")
    assert _evidence_supported("पचास हजारी रपये इस अकाउंट में ट्रांसफर", transcript)  # garbled copy
    assert not _evidence_supported("आपका आधार कार्ड ब्लॉक हो जाएगा", transcript)  # not in the call


def test_client_retries_connection_errors():
    attempts = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) < 3:
            raise httpx.ConnectError("getaddrinfo failed")
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"verdict":"SAFE","risk":3}'}}]})

    async def run():
        client = _client(handler)
        try:
            return await client.assess(LINES)
        finally:
            await client.close()

    v = asyncio.run(run())
    assert len(attempts) == 3 and v.verdict == "SAFE" and v.error is None
