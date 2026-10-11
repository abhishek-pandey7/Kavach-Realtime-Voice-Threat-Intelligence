"""Exotel AgentStream (bidirectional Voicebot) adapter for Merge-in mode.

Protocol (developer.exotel.com/docs/agentstream/websocket-protocol):
- Exotel -> us: connected, start (stream_sid, call_sid, media_format),
  media (base64 PCM16 mono, about every 100 ms), dtmf, mark, stop.
- us -> Exotel: media {payload}, mark {name}, clear. Outbound chunks must be
  3,200 to 100,000 bytes and a multiple of 320 bytes.
- Sample rate 8, 16 or 24 kHz, chosen with ?sample-rate= on the stream URL.
  Kavach asks for 16000 so audio goes to Prisma without resampling.

Not yet tested against a live Exotel account (waiting for AgentStream to be
enabled); written against the documented protocol.
"""

import asyncio
import base64
import json
import logging
import os
from collections.abc import AsyncIterator

import httpx
import numpy as np

from kavach.speak.timbre import Audio

log = logging.getLogger(__name__)

MIN_CHUNK, MAX_CHUNK, CHUNK_MULTIPLE = 3200, 100_000, 320


def outbound_chunks(pcm: bytes, sample_rate: int, chunk_ms: int = 200) -> list[bytes]:
    """Splits PCM into Exotel-legal chunks (padding the tail with silence)."""
    size = max(MIN_CHUNK, sample_rate * 2 * chunk_ms // 1000)
    size -= size % CHUNK_MULTIPLE
    size = min(size, MAX_CHUNK)
    chunks = [pcm[i:i + size] for i in range(0, len(pcm), size)]
    if chunks:
        tail = chunks[-1]
        padded = max(MIN_CHUNK, -(-len(tail) // CHUNK_MULTIPLE) * CHUNK_MULTIPLE)
        chunks[-1] = tail + b"\x00" * (padded - len(tail))
    return chunks


def resample_pcm16(pcm: bytes, src: int, dst: int) -> bytes:
    if src == dst or not pcm:
        return pcm
    x = np.frombuffer(pcm, dtype=np.int16).astype(np.float32)
    n = int(round(len(x) * dst / src))
    y = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)
    return np.clip(y, -32768, 32767).astype(np.int16).tobytes()


class ExotelStream:
    """Wraps one Exotel WebSocket: call audio in, Kavach's voice out.

    `ws` needs async receive_text() and send_text() (FastAPI's WebSocket).
    """

    def __init__(self, ws, target_rate: int = 16000):
        self.ws = ws
        self.target_rate = target_rate
        self.stream_sid: str | None = None
        self.call_sid: str | None = None
        self.sample_rate = 8000
        self.started = asyncio.Event()
        self.marks: dict[str, asyncio.Event] = {}
        self._mark_seq = 0

    async def audio(self) -> AsyncIterator[bytes]:
        """Yields caller-side audio at target_rate until the stream stops."""
        while True:
            event = json.loads(await self.ws.receive_text())
            kind = event.get("event")
            if kind == "start":
                start = event.get("start", {})
                self.stream_sid = start.get("stream_sid") or event.get("stream_sid")
                self.call_sid = start.get("call_sid")
                self.sample_rate = int(start.get("media_format", {}).get("sample_rate", 8000))
                self.started.set()
                log.info("Exotel stream %s started (call %s, %d Hz)", self.stream_sid, self.call_sid, self.sample_rate)
            elif kind == "media":
                pcm = base64.b64decode(event["media"]["payload"])
                yield resample_pcm16(pcm, self.sample_rate, self.target_rate)
            elif kind == "mark":
                name = event.get("mark", {}).get("name")
                if name in self.marks:
                    self.marks.pop(name).set()
            elif kind == "stop":
                log.info("Exotel stream stopped: %s", event.get("stop", {}).get("reason"))
                return

    async def speak(self, audio: Audio, wait: bool = True) -> None:
        """Plays audio into the call; waits for Exotel's playback mark by default."""
        await self.started.wait()
        pcm = resample_pcm16(audio.pcm, audio.sample_rate, self.sample_rate)
        for chunk in outbound_chunks(pcm, self.sample_rate):
            await self.ws.send_text(json.dumps({
                "event": "media", "stream_sid": self.stream_sid,
                "media": {"payload": base64.b64encode(chunk).decode("ascii")},
            }))
        self._mark_seq += 1
        name = f"kavach-{self._mark_seq}"
        done = asyncio.Event()
        self.marks[name] = done
        await self.ws.send_text(json.dumps({"event": "mark", "stream_sid": self.stream_sid, "mark": {"name": name}}))
        if wait:
            try:
                await asyncio.wait_for(done.wait(), timeout=audio.duration_s + 5)
            except asyncio.TimeoutError:
                log.warning("No playback mark from Exotel for %s", name)

    async def clear(self) -> None:
        await self.ws.send_text(json.dumps({"event": "clear", "stream_sid": self.stream_sid}))


async def place_call(to_number: str, stream_url: str) -> dict:
    """Asks Exotel to call `to_number` (a verified number) and stream it to us.

    Uses EXOTEL_SID, EXOTEL_API_KEY, EXOTEL_API_TOKEN, EXOTEL_CALLER_ID and
    EXOTEL_SUBDOMAIN (default api.in.exotel.com) from the environment.
    """
    sid = os.environ["EXOTEL_SID"]
    subdomain = os.environ.get("EXOTEL_SUBDOMAIN", "api.in.exotel.com")
    url = f"https://{subdomain}/v1/Accounts/{sid}/Calls/connect.json"
    data = {
        "From": to_number,
        "CallerId": os.environ["EXOTEL_CALLER_ID"],
        "StreamType": "bidirectional",
        "StreamUrl": stream_url,
    }
    auth = (os.environ["EXOTEL_API_KEY"], os.environ["EXOTEL_API_TOKEN"])
    async with httpx.AsyncClient(timeout=20) as http:
        resp = await http.post(url, data=data, auth=auth)
        resp.raise_for_status()
        return resp.json()
