import numpy as np

from kavach.eval import degrade
from kavach.eval.runner import CallResult, cer, edit_distance, summarise


def test_edit_distance_and_cer():
    assert edit_distance("kitten", "sitting") == 3
    assert cer("नमस्ते, आप कैसे हैं?", "नमस्ते आप कैसे हैं") == 0.0
    assert 0 < cer("पार्सल में ड्रग्स", "पार्सल में ड्रग") < 0.2


def test_add_noise_hits_target_snr():
    rng = np.random.default_rng(1)
    speech = (0.3 * np.sin(np.linspace(0, 2000, 16000))).astype(np.float32)
    noise = rng.standard_normal(16000).astype(np.float32)
    mixed = degrade.add_noise(speech, noise, snr_db=5.0)
    residual = mixed - speech
    snr = 10 * np.log10(np.mean(speech ** 2) / np.mean(residual ** 2))
    assert abs(snr - 5.0) < 0.2


def test_telephone_band_limits_and_resamples():
    t = np.arange(16000) / 16000
    tone_low, tone_high = np.sin(2 * np.pi * 1000 * t), np.sin(2 * np.pi * 6000 * t)
    y = degrade.telephone((0.4 * (tone_low + tone_high)).astype(np.float32), 16000)
    assert len(y) == 8000
    spectrum = np.abs(np.fft.rfft(y))
    freqs = np.fft.rfftfreq(len(y), 1 / 8000)
    assert spectrum[np.argmin(abs(freqs - 1000))] > 50 * spectrum[freqs > 3600].max()


def test_mulaw_roundtrip_is_close():
    x = np.linspace(-0.9, 0.9, 1000).astype(np.float32)
    assert np.max(np.abs(degrade.mulaw_roundtrip(x) - x)) < 0.03


def _r(label, condition, warned, t=None):
    return CallResult("c", label, "x", condition, "SOFT" if warned else "NONE", 70 if warned else 10,
                      warned, False, t, t, None, 0.1, "")


def test_summarise():
    rows = summarise([_r("scam", "phone", True, 20.0), _r("scam", "phone", False),
                      _r("genuine", "phone", False), _r("genuine", "phone", True, 5.0)])
    assert rows[0]["recall"] == 0.5 and rows[0]["false_alarm_rate"] == 0.5 and rows[0]["median_warn_s"] == 20.0
