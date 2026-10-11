# Text evaluation: keywords vs keywords + Evon

Each scripted call in `eval/calls/` is replayed turn by turn through Kavach's detector and risk scorer
(`scripts/text_eval.py`), with the same rules as the live pipeline: a SCAM verdict must survive a
3-sample majority vote before it can trigger a HARD warning. No audio, so no Gnani credits; Evon v3.3
(4-bit GGUF, llama.cpp on Kaggle 2×T4) runs greedily for the first verdict, 0.4 temperature for votes.

18 calls, all synthetic and written for this project: 9 scams, 9 genuine look-alikes.
Two identical runs on Oct 11, 2026 gave the same result.

| | Keywords only | Keywords + Evon |
|---|---|---|
| Correct | 13/18 | **17/18** |
| Scams warned | 4/9 | **8/9** (all HARD) |
| False alarms on genuine calls | 0/9 | **0/9** |

| Call | Label | Keywords only | Keywords + Evon |
|---|---|---|---|
| hi_bank_alert_genuine_01 | genuine | ✓ none | ✓ none |
| hi_bank_kyc_01 | scam | ✓ SOFT (turn 5) | ✓ HARD |
| hi_delivery_01 | genuine | ✓ watch | ✓ watch |
| hi_digital_arrest_01 | scam | ✓ SOFT (turn 8) | ✓ HARD |
| hi_electricity_genuine_01 | genuine | ✓ none | ✓ none |
| hi_electricity_scam_01 | scam | ✗ missed | ✓ HARD (turn 3) |
| hi_family_emergency_genuine_01 | genuine | ✓ none | ✓ none |
| hi_family_genuine_01 | genuine | ✓ none | ✓ none |
| hi_fedex_police_01 | scam | ✓ SOFT (turn 4) | ✓ HARD (turn 3) |
| hi_insurance_genuine_01 | genuine | ✓ none | ✓ none |
| hi_job_interview_genuine_01 | genuine | ✓ none | ✓ none |
| hi_kbc_lottery_01 | scam | ✗ watch only | ✓ HARD (turn 4) |
| hi_kyc_reworded_01 | scam | ✗ missed | ✓ HARD (turn 5) |
| hi_loan_offer_genuine_01 | genuine | ✓ none | ✓ none |
| hi_police_verification_genuine_01 | genuine | ✓ none | ✓ none |
| hi_relative_trouble_01 | scam | ✓ SOFT (turn 5) | ✓ HARD (turn 5) |
| hi_task_job_01 | scam | ✗ missed | ✗ missed |
| hi_upi_refund_01 | scam | ✗ watch only | ✓ HARD (turn 5) |

## Honest caveats

- **Tuned on these calls.** Two prompt rules were added after seeing misses on this set: an OTP can be
  described as "the code / the number that came on your phone", and a UPI PIN is never needed to receive
  money. Both are general facts, but results on this set are optimistic. Fresh, unseen calls (ideally
  human-written by someone else, and real recordings with consent) are needed to confirm.
- **Small and synthetic.** 18 calls written by the project, all Hindi. Not a benchmark.
- **Known miss:** the task-job scam (a fee for "premium tasks" with a promised 30% return). Evon does
  not treat an investment-style fee as a scam. Not tuned further, to avoid overfitting.
- **Variance:** with temperature 0.3 on every call, verdicts swung by 1 to 2 calls between identical
  runs. The greedy first pass made runs reproducible.
