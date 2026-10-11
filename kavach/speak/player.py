"""Plays audio through the local speaker (Kavach Guardian mode)."""

import asyncio

import numpy as np

from kavach.speak.timbre import Audio


async def play(audio: Audio, device: int | str | None = None) -> None:
    """Plays int16 mono audio and returns when playback finishes."""
    import sounddevice as sd

    samples = np.frombuffer(audio.pcm, dtype=np.int16)
    await asyncio.to_thread(_play_blocking, sd, samples, audio.sample_rate, device)


def _play_blocking(sd, samples, sample_rate: int, device) -> None:
    sd.play(samples, samplerate=sample_rate, device=device)
    sd.wait()
