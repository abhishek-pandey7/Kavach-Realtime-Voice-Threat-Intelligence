"""Audio sources that yield raw 16-bit mono PCM.

Every source produces little-endian int16 samples at the requested sample
rate. Frame sizes vary by source; use `Rechunker` to get the exact frame
size a consumer needs.
"""

import asyncio
import subprocess
from collections.abc import AsyncIterator
from pathlib import Path

SAMPLE_WIDTH = 2  # bytes per int16 sample


class Rechunker:
    """Splits an arbitrary byte stream into fixed-size frames."""

    def __init__(self, frame_bytes: int):
        self.frame_bytes = frame_bytes
        self._buf = bytearray()

    def push(self, data: bytes) -> list[bytes]:
        self._buf.extend(data)
        n = len(self._buf) // self.frame_bytes
        frames = [bytes(self._buf[i * self.frame_bytes:(i + 1) * self.frame_bytes]) for i in range(n)]
        del self._buf[:n * self.frame_bytes]
        return frames

    def flush(self) -> bytes | None:
        """Returns the leftover bytes zero-padded to a full frame, if any."""
        if not self._buf:
            return None
        frame = bytes(self._buf) + b"\x00" * (self.frame_bytes - len(self._buf))
        self._buf.clear()
        return frame


def decode_file(path: Path, sample_rate: int) -> bytes:
    """Decodes any audio file ffmpeg understands into mono int16 PCM."""
    cmd = [
        "ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(path),
        "-ac", "1", "-ar", str(sample_rate), "-f", "s16le", "-",
    ]
    return subprocess.run(cmd, check=True, capture_output=True).stdout


async def file_source(
    path: Path, sample_rate: int, chunk_ms: int = 20, realtime: bool = True
) -> AsyncIterator[bytes]:
    """Yields a file's audio in small chunks, paced like a live call by default."""
    pcm = decode_file(path, sample_rate)
    step = sample_rate * SAMPLE_WIDTH * chunk_ms // 1000
    loop = asyncio.get_running_loop()
    start = loop.time()
    for i, offset in enumerate(range(0, len(pcm), step)):
        if realtime:
            delay = start + i * chunk_ms / 1000 - loop.time()
            if delay > 0:
                await asyncio.sleep(delay)
        yield pcm[offset:offset + step]


async def mic_source(sample_rate: int, chunk_ms: int = 20, device: int | str | None = None) -> AsyncIterator[bytes]:
    """Yields live microphone audio until the consumer stops iterating."""
    import sounddevice as sd

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[bytes] = asyncio.Queue()

    def callback(indata, frames, time_info, status):  # runs on the audio thread
        loop.call_soon_threadsafe(queue.put_nowait, bytes(indata))

    blocksize = sample_rate * chunk_ms // 1000
    with sd.RawInputStream(
        samplerate=sample_rate, blocksize=blocksize, channels=1,
        dtype="int16", device=device, callback=callback,
    ):
        while True:
            yield await queue.get()
