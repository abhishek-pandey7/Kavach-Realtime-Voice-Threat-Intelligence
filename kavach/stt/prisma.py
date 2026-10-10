"""Streaming client for Gnani Prisma v2.5 speech-to-text.

Protocol (docs.gnani.ai/api/STT/stt-websocket):
- Connect to wss://api.vachana.ai/stt/v3/stream with config in headers.
- Send raw int16 mono PCM in binary frames of exactly 512 samples (1024 bytes),
  at real-time pace.
- Receive JSON events: connected, processing, transcript, error.
- With the undocumented `x-partials: true` header, Prisma instead sends
  speech_start, partial_transcript (about every 450 ms, with stable_text and
  volatile_text) and final_transcript events. Verified on Oct 11, 2026.
- A session lasts at most 15 minutes, so long calls rotate sessions.
"""

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass

import websockets

from kavach.audio.sources import Rechunker

log = logging.getLogger(__name__)

STREAM_URL = "wss://api.vachana.ai/stt/v3/stream"
FRAME_BYTES = 1024  # 512 int16 samples
LANGUAGES = ("bn-IN", "en-IN", "gu-IN", "hi-IN", "kn-IN", "ml-IN", "mr-IN", "pa-IN", "ta-IN", "te-IN")


@dataclass
class Transcript:
    text: str
    is_final: bool
    utterance_id: str
    segment_index: int
    audio_duration_ms: float
    latency_ms: float  # Prisma's own end-of-speech to transcript latency (finals only)
    received_at: float  # time.monotonic() when it arrived


@dataclass
class PrismaConfig:
    language: str = "hi-IN"
    sample_rate: int = 16000
    min_silence_ms: int = 300  # docs default 500; shorter means faster segments
    max_speech_s: float | None = 15.0  # force a segment during long monologues
    bias_words: list[str] | None = None  # word boosting, letter-only words, max 100
    bias_score: float | None = None  # 0.0, 0.5, 1.0, 1.5 or 2.0
    session_limit_s: float = 14 * 60  # rotate before the 15 minute cap
    partials: bool = True  # undocumented header; partial text roughly every 450 ms

    def headers(self, api_key: str) -> dict[str, str]:
        if self.language not in LANGUAGES:
            raise ValueError(f"Unsupported language {self.language!r}")
        headers = {
            "x-api-key-id": api_key,
            "lang_code": self.language,
            "x-sample-rate": str(self.sample_rate),
            "x-min-silence-ms": str(self.min_silence_ms),
        }
        if self.partials:
            headers["x-partials"] = "true"
        if self.max_speech_s:
            headers["x-max-speech-s"] = str(self.max_speech_s)
        if self.bias_words:
            headers["x-bias-list"] = json.dumps(self.bias_words[:100], ensure_ascii=False)
            if self.bias_score is not None:
                headers["x-bias-score"] = str(self.bias_score)
        return headers


class PrismaStream:
    def __init__(self, api_key: str, config: PrismaConfig | None = None):
        self.api_key = api_key
        self.config = config or PrismaConfig()

    async def transcribe(self, source: AsyncIterator[bytes], drain_s: float = 3.0) -> AsyncIterator[Transcript]:
        """Streams audio from `source` and yields transcripts as they arrive.

        When the source ends, sends a second of silence so the last utterance
        is closed, waits up to `drain_s` for remaining transcripts, then stops.
        """
        out: asyncio.Queue[Transcript | None] = asyncio.Queue()
        runner = asyncio.create_task(self._run(source, out, drain_s))
        try:
            while (item := await out.get()) is not None:
                yield item
        finally:
            runner.cancel()
            try:
                await runner
            except asyncio.CancelledError:
                pass

    async def _run(self, source: AsyncIterator[bytes], out: asyncio.Queue, drain_s: float) -> None:
        source_done = False
        try:
            while not source_done:
                source_done = await self._session(source, out, drain_s)
        finally:
            await out.put(None)

    async def _session(self, source: AsyncIterator[bytes], out: asyncio.Queue, drain_s: float) -> bool:
        """Runs one WebSocket session. Returns True when the source is exhausted."""
        cfg = self.config
        async with websockets.connect(
            STREAM_URL, additional_headers=cfg.headers(self.api_key), max_size=None
        ) as ws:
            receiver = asyncio.create_task(self._receive(ws, out))
            chunker = Rechunker(FRAME_BYTES)
            started = time.monotonic()
            exhausted = True
            async for chunk in source:
                for frame in chunker.push(chunk):
                    await ws.send(frame)
                if time.monotonic() - started > cfg.session_limit_s:
                    exhausted = False
                    break
            if (tail := chunker.flush()) is not None:
                await ws.send(tail)
            await self._send_silence(ws, seconds=1.0)
            try:
                await asyncio.wait_for(asyncio.shield(receiver), timeout=drain_s)
            except asyncio.TimeoutError:
                pass
            receiver.cancel()
            return exhausted

    async def _send_silence(self, ws, seconds: float) -> None:
        frame = b"\x00" * FRAME_BYTES
        frame_s = FRAME_BYTES / 2 / self.config.sample_rate
        for _ in range(int(seconds / frame_s)):
            await ws.send(frame)
            await asyncio.sleep(frame_s)

    async def _receive(self, ws, out: asyncio.Queue) -> None:
        try:
            async for message in ws:
                if isinstance(message, bytes):
                    continue
                event = json.loads(message)
                kind = event.get("type")
                if kind in ("transcript", "final_transcript", "partial_transcript"):
                    await out.put(_parse_transcript(event))
                elif kind == "error":
                    log.warning("Prisma error: %s", event.get("message"))
                elif kind == "connected":
                    log.info("Prisma connected: %s", event.get("config"))
        except websockets.ConnectionClosed as exc:
            log.info("Prisma session closed: %s", exc)


def _parse_transcript(event: dict) -> Transcript:
    is_final = event.get("type") != "partial_transcript"
    text = event.get("text")
    if not text:
        if is_final:
            text = event.get("output", {}).get("literal", "")
        else:
            text = f"{event.get('stable_text', '')} {event.get('volatile_text', '')}".strip()
    return Transcript(
        text=text,
        is_final=is_final,
        utterance_id=event.get("utterance_id") or event.get("segment_id", ""),
        segment_index=event.get("segment_index", event.get("seq", -1)),
        audio_duration_ms=event.get("audio_duration_ms", event.get("audio_ms", 0.0)),
        latency_ms=event.get("latency", 0.0),
        received_at=time.monotonic(),
    )
