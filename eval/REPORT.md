# Kavach evaluation report

Generated 2026-10-11 21:26. Evon: on.
6 scripted calls, all synthetic (voiced with Timbre v2.5). Small sample: treat these numbers as a smoke test, not a benchmark.

Conditions: `clean16k` original audio; `phone` 8 kHz, 300 to 3400 Hz, G.711 mu-law; `phone_snrN` noise mixed at N dB SNR before the phone channel. All audio is streamed to Prisma at 16 kHz (phone conditions are band-limited first).

Noise: generated pink noise plus 50 Hz mains hum. No recorded noise yet, so real-world noise (traffic, TV, crowds) may be harder than these numbers suggest.

## Summary

| Condition | Scam recall | HARD rate | False alarms | Median first warning | Median after first red flag | Mean CER |
|---|---|---|---|---|---|---|
| phone | 100% (3 calls) | 100% | 0% (3 calls) | 21.9 s | 17.6 s | 0.039 |
| phone_snr5 | 100% (3 calls) | 100% | 0% (3 calls) | 21.7 s | 16.4 s | 0.201 |
| phone_snr0 | 100% (3 calls) | 100% | 0% (3 calls) | 21.9 s | 16.4 s | 0.042 |

## Per call

| Call | Label | Condition | Level | Peak risk | First warning | Evon | CER |
|---|---|---|---|---|---|---|---|
| hi_bank_alert_genuine_01 | genuine | phone | NONE | 36 | – | SAFE | 0.050 |
| hi_bank_alert_genuine_01 | genuine | phone_snr0 | NONE | 36 | – | SAFE | 0.054 |
| hi_bank_alert_genuine_01 | genuine | phone_snr5 | NONE | 36 | – | SAFE | 0.050 |
| hi_bank_kyc_01 | scam | phone | HARD | 90 | 21.9 s | SCAM | 0.011 |
| hi_bank_kyc_01 | scam | phone_snr0 | HARD | 90 | 21.9 s | SCAM | 0.008 |
| hi_bank_kyc_01 | scam | phone_snr5 | HARD | 90 | 21.7 s | UNCERTAIN | 0.008 | error: ConnectionClosedError(None, None, None)
| hi_delivery_01 | genuine | phone | WATCH | 40 | – | SAFE | 0.018 |
| hi_delivery_01 | genuine | phone_snr0 | WATCH | 40 | – | SAFE | 0.041 |
| hi_delivery_01 | genuine | phone_snr5 | NONE | 0 | – | – | 1.000 | error: gaierror(11001, 'getaddrinfo failed')
| hi_digital_arrest_01 | scam | phone | HARD | 100 | 29.2 s | SCAM | 0.016 |
| hi_digital_arrest_01 | scam | phone_snr0 | HARD | 98 | 28.7 s | UNCERTAIN | 0.016 |
| hi_digital_arrest_01 | scam | phone_snr5 | HARD | 100 | 29.0 s | SCAM | 0.014 |
| hi_family_genuine_01 | genuine | phone | NONE | 0 | – | SAFE | 0.073 |
| hi_family_genuine_01 | genuine | phone_snr0 | NONE | 0 | – | SAFE | 0.073 |
| hi_family_genuine_01 | genuine | phone_snr5 | NONE | 0 | – | SAFE | 0.073 |
| hi_relative_trouble_01 | scam | phone | HARD | 90 | 20.3 s | SCAM | 0.066 |
| hi_relative_trouble_01 | scam | phone_snr0 | HARD | 90 | 19.4 s | SCAM | 0.061 |
| hi_relative_trouble_01 | scam | phone_snr5 | HARD | 90 | 20.4 s | SCAM | 0.061 |
