# Kavach evaluation report

Generated 2026-10-11 09:58. Evon: off (keywords only, so HARD is impossible by design).
6 scripted calls, all synthetic (voiced with Timbre v2.5). Small sample: treat these numbers as a smoke test, not a benchmark.

Conditions: `clean16k` original audio; `phone` 8 kHz, 300 to 3400 Hz, G.711 mu-law; `phone_snrN` noise mixed at N dB SNR before the phone channel. All audio is streamed to Prisma at 16 kHz (phone conditions are band-limited first).

Noise: generated pink noise plus 50 Hz mains hum. No recorded noise yet, so real-world noise (traffic, TV, crowds) may be harder than these numbers suggest.

## Summary

| Condition | Scam recall | HARD rate | False alarms | Median first warning | Median after first red flag | Mean CER |
|---|---|---|---|---|---|---|
| phone | 100% (3 calls) | 0% | 0% (3 calls) | 21.8 s | 17.6 s | 0.039 |
| phone_snr10 | 100% (3 calls) | 0% | 0% (3 calls) | 22.2 s | 17.5 s | 0.038 |
| phone_snr5 | 100% (3 calls) | 0% | 0% (3 calls) | 22.2 s | 16.4 s | 0.040 |
| phone_snr0 | 100% (3 calls) | 0% | 0% (3 calls) | 22.3 s | 16.3 s | 0.042 |

## Per call

| Call | Label | Condition | Level | Peak risk | First warning | Evon | CER |
|---|---|---|---|---|---|---|---|
| hi_bank_alert_genuine_01 | genuine | phone | NONE | 36 | – | – | 0.050 |
| hi_bank_alert_genuine_01 | genuine | phone_snr0 | NONE | 36 | – | – | 0.054 |
| hi_bank_alert_genuine_01 | genuine | phone_snr10 | NONE | 36 | – | – | 0.050 |
| hi_bank_alert_genuine_01 | genuine | phone_snr5 | NONE | 36 | – | – | 0.050 |
| hi_bank_kyc_01 | scam | phone | SOFT | 78 | 21.8 s | – | 0.011 |
| hi_bank_kyc_01 | scam | phone_snr0 | SOFT | 78 | 21.7 s | – | 0.008 |
| hi_bank_kyc_01 | scam | phone_snr10 | SOFT | 78 | 21.7 s | – | 0.008 |
| hi_bank_kyc_01 | scam | phone_snr5 | SOFT | 78 | 21.6 s | – | 0.008 |
| hi_delivery_01 | genuine | phone | WATCH | 40 | – | – | 0.018 |
| hi_delivery_01 | genuine | phone_snr0 | WATCH | 40 | – | – | 0.041 |
| hi_delivery_01 | genuine | phone_snr10 | WATCH | 40 | – | – | 0.023 |
| hi_delivery_01 | genuine | phone_snr5 | WATCH | 40 | – | – | 0.032 |
| hi_digital_arrest_01 | scam | phone | SOFT | 84 | 35.0 s | – | 0.016 |
| hi_digital_arrest_01 | scam | phone_snr0 | SOFT | 84 | 35.2 s | – | 0.016 |
| hi_digital_arrest_01 | scam | phone_snr10 | SOFT | 84 | 35.2 s | – | 0.016 |
| hi_digital_arrest_01 | scam | phone_snr5 | SOFT | 84 | 35.2 s | – | 0.014 |
| hi_family_genuine_01 | genuine | phone | NONE | 0 | – | – | 0.073 |
| hi_family_genuine_01 | genuine | phone_snr0 | NONE | 0 | – | – | 0.073 |
| hi_family_genuine_01 | genuine | phone_snr10 | NONE | 0 | – | – | 0.073 |
| hi_family_genuine_01 | genuine | phone_snr5 | NONE | 0 | – | – | 0.073 |
| hi_relative_trouble_01 | scam | phone | SOFT | 76 | 21.7 s | – | 0.066 |
| hi_relative_trouble_01 | scam | phone_snr0 | SOFT | 76 | 22.3 s | – | 0.061 |
| hi_relative_trouble_01 | scam | phone_snr10 | SOFT | 76 | 22.2 s | – | 0.061 |
| hi_relative_trouble_01 | scam | phone_snr5 | SOFT | 76 | 22.2 s | – | 0.061 |
