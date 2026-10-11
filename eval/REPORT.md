# Kavach evaluation report

Generated 2026-10-12 00:05. Evon: on.
18 scripted calls, all synthetic (voiced with Timbre v2.5). Small sample: treat these numbers as a smoke test, not a benchmark.

Conditions: `clean16k` original audio; `phone` 8 kHz, 300 to 3400 Hz, G.711 mu-law; `phone_snrN` noise mixed at N dB SNR before the phone channel. All audio is streamed to Prisma at 16 kHz (phone conditions are band-limited first).

Noise: generated pink noise plus 50 Hz mains hum. No recorded noise yet, so real-world noise (traffic, TV, crowds) may be harder than these numbers suggest.

## Summary

| Condition | Scam recall | HARD rate | False alarms | Median first warning | Median after first red flag | Mean CER |
|---|---|---|---|---|---|---|
| phone | 100% (9 calls) | 100% | 0% (9 calls) | 27.1 s | 15.9 s | 0.053 |
| phone_snr5 | 100% (9 calls) | 100% | 0% (9 calls) | 25.2 s | 12.3 s | 0.054 |

## Per call

| Call | Label | Condition | Level | Peak risk | First warning | Evon | CER |
|---|---|---|---|---|---|---|---|
| hi_bank_alert_genuine_01 | genuine | phone | NONE | 36 | – | SAFE | 0.050 |
| hi_bank_alert_genuine_01 | genuine | phone_snr5 | NONE | 36 | – | SAFE | 0.050 |
| hi_bank_kyc_01 | scam | phone | HARD | 90 | 21.8 s | SCAM | 0.011 |
| hi_bank_kyc_01 | scam | phone_snr5 | HARD | 90 | 21.8 s | SCAM | 0.008 |
| hi_delivery_01 | genuine | phone | WATCH | 40 | – | SAFE | 0.018 |
| hi_delivery_01 | genuine | phone_snr5 | WATCH | 40 | – | SAFE | 0.032 |
| hi_digital_arrest_01 | scam | phone | HARD | 100 | 27.1 s | SCAM | 0.016 |
| hi_digital_arrest_01 | scam | phone_snr5 | HARD | 100 | 35.4 s | SCAM | 0.014 |
| hi_electricity_genuine_01 | genuine | phone | NONE | 0 | – | SAFE | 0.036 |
| hi_electricity_genuine_01 | genuine | phone_snr5 | NONE | 0 | – | SAFE | 0.032 |
| hi_electricity_scam_01 | scam | phone | HARD | 90 | 19.7 s | SCAM | 0.059 |
| hi_electricity_scam_01 | scam | phone_snr5 | HARD | 90 | 19.4 s | SCAM | 0.059 |
| hi_family_emergency_genuine_01 | genuine | phone | NONE | 0 | – | UNCERTAIN | 0.080 |
| hi_family_emergency_genuine_01 | genuine | phone_snr5 | NONE | 0 | – | SAFE | 0.080 |
| hi_family_genuine_01 | genuine | phone | NONE | 0 | – | SAFE | 0.073 |
| hi_family_genuine_01 | genuine | phone_snr5 | NONE | 0 | – | SAFE | 0.073 |
| hi_fedex_police_01 | scam | phone | HARD | 98 | 29.6 s | SCAM | 0.002 |
| hi_fedex_police_01 | scam | phone_snr5 | HARD | 98 | 25.2 s | UNCERTAIN | 0.004 |
| hi_insurance_genuine_01 | genuine | phone | NONE | 0 | – | SAFE | 0.044 |
| hi_insurance_genuine_01 | genuine | phone_snr5 | NONE | 0 | – | SAFE | 0.072 |
| hi_job_interview_genuine_01 | genuine | phone | NONE | 0 | – | SAFE | 0.041 |
| hi_job_interview_genuine_01 | genuine | phone_snr5 | NONE | 0 | – | SAFE | 0.041 |
| hi_kbc_lottery_01 | scam | phone | HARD | 95 | 21.0 s | SCAM | 0.136 |
| hi_kbc_lottery_01 | scam | phone_snr5 | HARD | 90 | 15.9 s | SCAM | 0.148 |
| hi_kyc_reworded_01 | scam | phone | HARD | 85 | 37.9 s | SCAM | 0.039 |
| hi_kyc_reworded_01 | scam | phone_snr5 | HARD | 85 | 35.8 s | SCAM | 0.008 |
| hi_loan_offer_genuine_01 | genuine | phone | NONE | 0 | – | SAFE | 0.045 |
| hi_loan_offer_genuine_01 | genuine | phone_snr5 | NONE | 0 | – | SAFE | 0.050 |
| hi_police_verification_genuine_01 | genuine | phone | NONE | 30 | – | SAFE | 0.060 |
| hi_police_verification_genuine_01 | genuine | phone_snr5 | NONE | 30 | – | SAFE | 0.043 |
| hi_relative_trouble_01 | scam | phone | HARD | 90 | 22.6 s | SCAM | 0.066 |
| hi_relative_trouble_01 | scam | phone_snr5 | HARD | 90 | 22.4 s | SCAM | 0.061 |
| hi_task_job_01 | scam | phone | HARD | 90 | 41.2 s | SCAM | 0.131 |
| hi_task_job_01 | scam | phone_snr5 | HARD | 90 | 37.5 s | SCAM | 0.156 |
| hi_upi_refund_01 | scam | phone | HARD | 90 | 33.0 s | SCAM | 0.049 |
| hi_upi_refund_01 | scam | phone_snr5 | HARD | 95 | 32.6 s | SCAM | 0.046 |
