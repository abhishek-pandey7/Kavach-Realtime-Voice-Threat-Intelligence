"""Makes clean synthetic calls sound like real phone audio.

- telephone(): 300 to 3400 Hz band limit, 8 kHz, G.711 mu-law round trip
- add_noise(): mixes noise at a target signal-to-noise ratio
- Noise sources: generated (white, pink, brown, hum) or any WAV files placed
  in cache/noise/ (e.g. MUSAN noises or your own recordings of traffic, a
  pressure cooker or a ceiling fan). See docs/RESEARCH.md, MUSAN.

Everything works on float32 arrays in [-1, 1].
"""

from pathlib import Path

import numpy as np

from kavach.audio.sources import decode_file

MU = 255.0


def load(path: Path, sample_rate: int) -> np.ndarray:
    pcm = decode_file(path, sample_rate)
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0


def to_pcm16(x: np.ndarray) -> bytes:
    return (np.clip(x, -1.0, 1.0) * 32767.0).astype(np.int16).tobytes()


def resample(x: np.ndarray, src: int, dst: int) -> np.ndarray:
    if src == dst:
        return x
    n = int(round(len(x) * dst / src))
    spectrum = np.fft.rfft(x)
    keep = min(len(spectrum), n // 2 + 1)
    out = np.zeros(n // 2 + 1, dtype=complex)
    out[:keep] = spectrum[:keep]
    return (np.fft.irfft(out, n) * (n / len(x))).astype(np.float32)


def bandpass(x: np.ndarray, sample_rate: int, low: float = 300.0, high: float = 3400.0) -> np.ndarray:
    spectrum = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1.0 / sample_rate)
    spectrum[(freqs < low) | (freqs > high)] = 0
    return np.fft.irfft(spectrum, len(x)).astype(np.float32)


def mulaw_roundtrip(x: np.ndarray) -> np.ndarray:
    """Quantises through 8-bit G.711 mu-law and back."""
    x = np.clip(x, -1.0, 1.0)
    encoded = np.sign(x) * np.log1p(MU * np.abs(x)) / np.log1p(MU)
    quantised = np.round((encoded + 1) / 2 * 255) / 255 * 2 - 1
    return (np.sign(quantised) * (np.power(1 + MU, np.abs(quantised)) - 1) / MU).astype(np.float32)


def telephone(x: np.ndarray, sample_rate: int) -> np.ndarray:
    """Returns 8 kHz narrowband, mu-law coded audio."""
    y = resample(x, sample_rate, 8000)
    return mulaw_roundtrip(bandpass(y, 8000))


def generated_noise(kind: str, n: int, sample_rate: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    white = rng.standard_normal(n).astype(np.float32)
    if kind == "white":
        return white
    if kind == "hum":  # mains hum with harmonics, like a cheap charger or fan
        t = np.arange(n) / sample_rate
        return sum(np.sin(2 * np.pi * 50 * k * t) / k for k in (1, 2, 3, 5)).astype(np.float32)
    spectrum = np.fft.rfft(white)
    freqs = np.maximum(np.fft.rfftfreq(n, 1.0 / sample_rate), 1.0)
    spectrum /= np.sqrt(freqs) if kind == "pink" else freqs  # brown otherwise
    return np.fft.irfft(spectrum, n).astype(np.float32)


def file_noise(path: Path, n: int, sample_rate: int) -> np.ndarray:
    noise = load(path, sample_rate)
    reps = int(np.ceil(n / max(len(noise), 1)))
    return np.tile(noise, reps)[:n]


def add_noise(x: np.ndarray, noise: np.ndarray, snr_db: float) -> np.ndarray:
    """Scales noise so that 10*log10(P_signal / P_noise) == snr_db."""
    speech = x[np.abs(x) > 1e-4]  # ignore silent gaps when measuring speech power
    p_signal = float(np.mean(speech ** 2)) if len(speech) else 1e-8
    p_noise = float(np.mean(noise ** 2)) or 1e-12
    gain = np.sqrt(p_signal / (p_noise * 10 ** (snr_db / 10)))
    y = x + gain * noise[: len(x)]
    peak = float(np.max(np.abs(y))) or 1.0
    return (y / peak * 0.9 if peak > 0.99 else y).astype(np.float32)
