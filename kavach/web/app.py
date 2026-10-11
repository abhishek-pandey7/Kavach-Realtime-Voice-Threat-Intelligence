"""Live dashboard: runs a Kavach session and streams its events to browsers.

    python -m kavach.web.app            # then open http://localhost:8765

The page can start a session on a recorded call (cache/calls/*.wav) or the
microphone (Guardian mode), with or without Evon.
"""

import asyncio
import json
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from kavach.alerts.telegram import TelegramAlerter
from kavach.audio.sources import file_source, mic_source
from kavach.config import CACHE_DIR, gnani_api_key
from kavach.detect.evon import EvonClient
from kavach.detect.keywords import KeywordDetector
from kavach.pipeline import KavachSession, RecordingSpeaker, SessionConfig
from kavach.speak.player import play
from kavach.speak.timbre import TimbreClient, load_voice
from kavach.stt.prisma import PrismaConfig, PrismaStream

log = logging.getLogger(__name__)
STATIC = Path(__file__).parent / "static"
CALLS = CACHE_DIR / "calls"

app = FastAPI(title="Kavach")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class Hub:
    """Fan-out of session events to every connected browser."""

    def __init__(self):
        self.clients: set[WebSocket] = set()
        self.history: list[dict] = []  # replayed to late joiners

    async def publish(self, event: dict) -> None:
        self.history.append(event)
        message = json.dumps(event, ensure_ascii=False)
        for ws in list(self.clients):
            try:
                await ws.send_text(message)
            except Exception:
                self.clients.discard(ws)


hub = Hub()
detector = KeywordDetector()
state: dict = {"task": None}


class StartRequest(BaseModel):
    source: str = "file"  # "file" or "mic"
    file: str | None = None
    language: str = "hi-IN"
    rate: int = 8000
    evon: bool = False
    speaker: str = "record"  # "record" or "local"
    family_voice: str | None = None


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/calls")
async def calls():
    return sorted(p.name for p in CALLS.glob("*.wav")) if CALLS.exists() else []


@app.get("/api/calls/{name}")
async def call_audio(name: str):
    path = (CALLS / name).resolve()
    if path.parent != CALLS.resolve() or not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path, media_type="audio/wav")


@app.get("/api/speech")
async def speech(text: str, lang: str = "hi-IN", voice: str | None = None):
    """Warning audio for in-browser playback (served from the Timbre cache)."""
    import io
    import wave

    timbre = TimbreClient()
    embedding = load_voice(voice) if voice else None
    if embedding:
        audio = await asyncio.to_thread(timbre.speak_cloned, text, embedding)
    else:
        audio = await asyncio.to_thread(timbre.speak, text, lang)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(audio.sample_rate)
        w.writeframes(audio.pcm)
    from fastapi.responses import Response
    return Response(buf.getvalue(), media_type="audio/wav")


@app.post("/api/start")
async def start(req: StartRequest):
    if state["task"] and not state["task"].done():
        return JSONResponse({"error": "a session is already running"}, status_code=409)
    if req.source == "file":
        path = (CALLS / (req.file or "")).resolve()
        if path.parent != CALLS.resolve() or not path.exists():
            return JSONResponse({"error": "unknown call file"}, status_code=400)
        source = file_source(path, 16000, via_rate=req.rate if req.rate != 16000 else None)
    else:
        source = mic_source(16000)
    hub.history.clear()
    state["task"] = asyncio.create_task(_run(req, source))
    return {"ok": True}


@app.post("/api/stop")
async def stop():
    task = state["task"]
    if task and not task.done():
        task.cancel()
    return {"ok": True}


async def _run(req: StartRequest, source) -> None:
    await hub.publish({"t": 0, "type": "start", "source": req.source, "file": req.file,
                       "language": req.language, "evon": req.evon})
    evon = EvonClient() if req.evon else None
    config = SessionConfig(
        language=req.language, echo_guard=req.source == "mic",
        family_voice=load_voice(req.family_voice) if req.family_voice else None,
    )
    session = KavachSession(
        config, detector, TimbreClient(), play if req.speaker == "local" else RecordingSpeaker(),
        evon=evon, alerter=TelegramAlerter(), on_event=hub.publish,
    )
    prisma = PrismaStream(gnani_api_key(), PrismaConfig(language=req.language))
    try:
        await session.process(prisma.transcribe(source))
    except asyncio.CancelledError:
        await hub.publish({"t": session._elapsed(), "type": "end", "report": session.report(), "stopped": True})
    except Exception as exc:  # surface failures on the dashboard
        log.exception("session failed")
        await hub.publish({"t": session._elapsed(), "type": "error", "message": repr(exc)})
    finally:
        if evon:
            await evon.close()


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    for event in hub.history:
        await ws.send_text(json.dumps(event, ensure_ascii=False))
    hub.clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        hub.clients.discard(ws)


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="127.0.0.1", port=8765)
