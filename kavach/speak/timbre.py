"""Gnani Timbre v2.5 text-to-speech and voice cloning, with a disk cache.

Warnings are mostly fixed sentences, so each (text, voice, format) is
synthesised once and replayed from cache/tts/. This keeps Gnani credit use
low during development, testing and filming.
"""

import base64
import hashlib
import io
import json
import wave
from dataclasses import dataclass
from pathlib import Path

import httpx

from kavach.config import CACHE_DIR, gnani_api_key

TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"
CLONE_URL = "https://api.vachana.ai/api/v1/tts/voice-clone/embeddings"

# Calm voices per language for warnings (docs: TTS available voices).
DEFAULT_VOICES = {
    "hi-IN": "Nalini", "en-IN": "Kaveri", "hi-en": "Poorvi", "ta-IN": "Brinda",
    "bn-IN": "Kirra", "te-IN": "Lavanya", "kn-IN": "Saanvi", "ml-IN": "Reshma",
    "mr-IN": "Zahira", "gu-IN": "Falak", "pa-IN": "Mehuli",
}


@dataclass
class Audio:
    pcm: bytes  # int16 mono
    sample_rate: int

    @classmethod
    def from_wav(cls, data: bytes) -> "Audio":
        with wave.open(io.BytesIO(data)) as w:
            if w.getsampwidth() != 2 or w.getnchannels() != 1:
                raise ValueError("expected 16-bit mono WAV")
            return cls(w.readframes(w.getnframes()), w.getframerate())

    @property
    def duration_s(self) -> float:
        return len(self.pcm) / 2 / self.sample_rate


def _audio_config(sample_rate: int) -> dict:
    return {"sample_rate": sample_rate, "num_channels": 1, "sample_width": 2,
            "encoding": "linear_pcm", "container": "wav"}


class TimbreClient:
    def __init__(self, api_key: str | None = None, cache_dir: Path = CACHE_DIR / "tts",
                 transport: httpx.BaseTransport | None = None):
        self.api_key = api_key or gnani_api_key()
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._http = httpx.Client(headers={"X-API-Key-ID": self.api_key}, timeout=30, transport=transport)
        self.api_calls = 0

    def _cached(self, key_parts: list[str], request: dict) -> Audio:
        key = hashlib.sha1("\x1f".join(key_parts).encode("utf-8")).hexdigest()[:20]
        path = self.cache_dir / f"{key}.wav"
        if not path.exists():
            resp = self._http.post(TTS_URL, json=request)
            if resp.status_code != 200 or not resp.headers.get("content-type", "").startswith("audio"):
                raise RuntimeError(f"Timbre failed ({resp.status_code}): {resp.text[:300]}")
            self.api_calls += 1
            path.write_bytes(resp.content)
        return Audio.from_wav(path.read_bytes())

    def speak(self, text: str, language: str = "hi-IN", voice: str | None = None,
              sample_rate: int = 16000, speed: float = 0.95) -> Audio:
        """Synthesises text with a stock Timbre voice (cached)."""
        voice = voice or DEFAULT_VOICES.get(language, "Nalini")
        request = {"text": text, "voice": voice, "model": "timbre-v2.5", "language": language,
                   "speed": speed, "audio_config": _audio_config(sample_rate)}
        return self._cached(["stock", text, voice, language, str(sample_rate), str(speed)], request)

    def speak_cloned(self, text: str, embedding: dict, sample_rate: int = 16000) -> Audio:
        """Synthesises text in a cloned voice (cached). `embedding` comes from clone()."""
        request = {"text": text, "model": "vachana-vc-v1", "speaker_embedding": embedding,
                   "audio_config": _audio_config(sample_rate)}
        fingerprint = hashlib.sha1(embedding["embedding"].encode()).hexdigest()[:12]
        return self._cached(["clone", text, fingerprint, str(sample_rate)], request)

    def clone(self, reference_audio: Path) -> dict:
        """Creates a voice embedding from 5 to 30 s of clean, consented speech."""
        with reference_audio.open("rb") as f:
            resp = self._http.post(CLONE_URL, files={"audio_file": (reference_audio.name, f)})
        resp.raise_for_status()
        self.api_calls += 1
        return resp.json()["data"]["voice_clone_embedding"]


def save_voice(name: str, embedding: dict) -> Path:
    path = CACHE_DIR / "voices" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(embedding), encoding="utf-8")
    return path


def load_voice(name: str) -> dict | None:
    path = CACHE_DIR / "voices" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def pcm_to_base64(audio: Audio) -> str:
    return base64.b64encode(audio.pcm).decode("ascii")
