# Kavach: Realtime Voice Threat Intelligence

**Kavach listens to a phone call as it happens, recognises scam scripts in Indian languages, and speaks a warning into the call before any money moves.**

Built for Gnani AI's [Great Indian AI Internship Challenge](https://www.gnani.ai/internship) ("Build Sovereign AI for India"), entirely on Gnani AI's own speech and language models.

> Status: working prototype in active development (October 2026). All data used in this project is synthetic or staged with consent. See [Data and privacy](#data-and-privacy).

---

## The problem

India's phone scams are now scripted, multilingual and live. In a "digital arrest" scam, a caller poses as CBI, police or customs, claims a parcel in the victim's name contained drugs, orders them to stay on the call and tell no one, and pressures them into "verification" payments. Government data cited by [Bloomberg](https://www.bloomberg.com/opinion/features/2025-10-12/digital-arrests-inside-india-s-scariest-scam-and-how-to-stop-it) puts losses to digital arrest scams alone at ₹25.8 billion since 2022. Fake KYC, courier, UPI refund and "your son is in trouble" calls follow the same pattern.

Existing defences don't reach the moment that matters:

- **Caller-ID spam labels** fail when the scammer uses a fresh number.
- **Awareness campaigns and advice** arrive after the call, when the money is already gone.
- **On-device scam detection** from big platforms, such as [Google's Scam Detection](https://blog.google/security/new-ai-powered-scam-detection-features/), launched for English calls on selected smartphones. It does not reach a parent on a basic phone who speaks Bhojpuri or Tamil.

The people targeted most often (elderly parents, non-English speakers, smaller towns) need protection **during** the call, **in their own language**.

## What Kavach does

1. **Listens** to the call in real time, including noisy, code-mixed speech like Hinglish.
2. **Understands** what is being said and tracks how the conversation develops: fake authority, then threat, then isolation ("kisi ko mat batana"), then payment demand.
3. **Speaks into the call.** The person hears a calm warning in their own language, optionally in a family member's cloned voice (with consent). The scammer hears that the call is being monitored.
4. **Alerts the family** with a short summary of what was said and why it was flagged.
5. **Debriefs afterwards** in the user's language, and prepares a draft report for India's 1930 cybercrime helpline.

### Two ways to use it

| Mode | How it works | Status |
|---|---|---|
| **Kavach Guardian** | A spare Android phone or laptop sits near the user. When a call is on speakerphone, Guardian listens through its mic and speaks warnings out loud, which the caller also hears. Works with any phone, including feature phones and landlines. | Primary |
| **Merge-in Kavach** | The user taps "Bulao Kavach". Kavach calls them through a telephony provider (Exotel) and they merge it into the suspicious call. Kavach then hears real telephone audio and speaks directly into the call. | Planned, depends on telephony access |

---

## Built on Gnani AI's models

Every step that hears, reasons or speaks runs on a Gnani AI model. No other speech or language model is used in the product.

| Gnani model | Role in Kavach | How we use it |
|---|---|---|
| **Prisma v2.5** (speech to text) | The ears | Streaming WebSocket transcription of call audio at 8 kHz (telephone) or 16 kHz (speakerphone), across Hindi, Hinglish, Tamil, Bengali and more. REST and batch endpoints for the evaluation set. |
| **Evon v3.3** (reasoning LLM, open weights) | The brain | Self-hosted. Reads the rolling transcript and returns a structured verdict: scam type, red flags, quoted evidence, risk score, and the warning to speak. Also writes the post-call debrief and generates synthetic test calls. |
| **Timbre v2.5** (text to speech) | The voice | Streams the warning back in the listener's language, at 8 kHz straight into a phone line or at higher quality through a speaker. |
| **Gnani voice cloning** | The familiar voice | Speaks the warning in a consenting family member's voice, which a frightened listener is more likely to trust. |

Self-hosting Evon means call transcripts are reasoned over on infrastructure we control, not sent to a foreign API. A tool that listens to private calls should work this way, and it matches the challenge's sovereign AI theme.

---

## How it works

```
 Audio source ───────────────────────────────────────────────────────────────┐
   Guardian: device microphone (speakerphone)                                 │
   Merge-in: Exotel bidirectional stream (8 kHz telephone audio)              │
                                                                              ▼
 [1] Prisma v2.5 streaming STT  ──>  utterance transcripts (code-mixed, multilingual)
                                                                              │
                                                                              ▼
 [2] Detection engine
       L1  Red-flag lexicon (instant, explainable, per language)
       L2  Evon v3.3 over a rolling window of the whole call so far
           -> verdict: SAFE / UNCERTAIN / SCAM, scam type, tactic stage, red flags, evidence
       Risk scorer: fuses L1 + L2, tracks tactic progression, applies hysteresis
                                                                              │
                     ┌────────────────────────────────────────────────────────┤
                     ▼                                                        ▼
 [3] Timbre v2.5 / voice clone                                    Family alert + live dashboard
     spoken warning into the call                                 post-call debrief (Evon)
```

### Detection design

- **Two layers.** A fast keyword layer catches obvious phrases within milliseconds. Evon handles meaning, context and phrasing the lexicon has never seen.
- **Whole-call context, not single sentences.** Research on LLM-based real-time scam detection found that judging each utterance with little context causes false alarms on innocent words like "payment" ([Shen et al., 2025](https://arxiv.org/abs/2502.03964)). Evon always sees the conversation so far.
- **An explicit "UNCERTAIN" state.** The same work showed that letting the model defer when evidence is thin raises precision. Kavach stays quiet while uncertain and escalates only when the evidence builds.
- **Tactic progression.** Scams follow a sequence: hook, fake authority, threat, isolation, payment. Kavach tracks which stages have appeared and warns on the trajectory, not on single keywords. This follows work that treats vishing defence as forecasting harm before it happens ([Lee et al., 2026](https://arxiv.org/abs/2609.07151)) and earlier work on predicting where a conversation is heading ([Chang and Danescu-Niculescu-Mizil, 2019](https://aclanthology.org/D19-1481/)).
- **Grounded in scam psychology.** Red-flag categories (authority, urgency, secrecy, isolation, payment and credential requests) draw on documented principles of how scammers exploit victims ([Stajano and Wilson, 2011](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-754.html)).
- **Escalation ladder.** Watch (dashboard only), then soft warning (to the user), then hard warning (into the call, family alerted). Warning too early feels like "jumping to conclusions" and too late is useless, so timing is tuned on data.
- **No denoising before transcription.** Speech enhancement can introduce artifacts that hurt recognition more than the noise itself ([Iwamoto et al., 2022](https://arxiv.org/abs/2201.06685)). Prisma is trained on noisy telephone audio, so raw audio goes straight in.

### Latency targets

| Step | Target |
|---|---|
| End of utterance to Prisma transcript | under 0.8 s |
| Keyword layer | under 10 ms |
| Evon verdict | under 2 s |
| Timbre first audio | under 0.7 s |
| **Red-flag phrase spoken to warning starts** | **under 4 s** |

These are targets. Measured numbers will replace them as the build progresses.

---

## Evaluation

Real scam recordings contain other people's voices and personal data, so Kavach is evaluated on synthetic and staged calls, following the approach of recent telecom fraud datasets ([TeleAntiFraud-28k, Ma et al., 2025](https://arxiv.org/abs/2503.24115)).

- **Scam calls** across seven types (digital arrest, courier/customs, bank KYC, UPI refund, relative in trouble, utility disconnection, prize/job), written with Evon and voiced with Timbre.
- **Hard negatives:** genuine-sounding bank fraud alerts, delivery calls, bill reminders and relatives asking for money. A detector that flags every bank call is useless, so false alarms are measured as carefully as detections ([TeleAntiFraud 2.0](https://arxiv.org/abs/2609.18748) makes the same point about near-domain lawful calls).
- **Human-recorded staged calls** with consenting actors, because TTS audio is cleaner than real speech.
- **Noise and channel:** background noise mixed at several signal-to-noise levels (including [MUSAN](https://arxiv.org/abs/1510.08484) noises and Indian household sounds), then passed through 8 kHz G.711 telephone coding and a speakerphone re-recording.
- **Paraphrase robustness:** LLMs can rewrite scam scripts to slip past classifiers ([Li et al., 2025](https://arxiv.org/abs/2507.16291)), so the test set includes rewritten versions of each scam.
- **Metrics:** scam recall, false alarm rate on hard negatives, median time from first red flag to warning, and Prisma word/character error rate per language and noise level. Ablations compare keywords only, Evon only, and both.

Results will be published in `eval/REPORT.md`, including where Kavach fails.

---

## Data and privacy

- **Synthetic data only.** No real phone numbers, account numbers, Aadhaar, PAN or recorded calls, in line with the challenge rules and India's DPDP Act.
- **Consent.** Everyone appearing in demos has consented. Voices are cloned only from people who agreed to it, for their own family's use.
- **No storage by default.** Call audio is processed in memory. Transcripts are kept only in demo mode.
- **Minimal exposure.** Numbers that look like OTPs, account numbers or card numbers are masked before reasoning, inspired by modular transcript sanitisation for scam detection ([Wang et al., 2025](https://arxiv.org/abs/2510.18493)).
- **Self-hosted reasoning.** Evon runs on our own GPU.

---

## Research foundations

Full notes, including what each paper changed in our design, are in [docs/RESEARCH.md](docs/RESEARCH.md).

| Paper | What we take from it |
|---|---|
| Shen et al., *"It Warned Me Just at the Right Moment": Exploring LLM-based Real-time Detection of Phone Scams*, 2025 ([arXiv:2502.03964](https://arxiv.org/abs/2502.03964)) | Turn-by-turn detection with whole-call context, the UNCERTAIN label, and the precision vs. recall vs. timeliness trade-off |
| Shen et al., *Combating Phone Scams with LLM-based Detection: Where Do We Stand?*, AAAI 2025 student abstract ([arXiv:2409.11643](https://arxiv.org/abs/2409.11643)) | Known failure modes: biased datasets, low recall, hallucinated reasoning |
| Ma et al., *TeleAntiFraud-28k: An Audio-Text Slow-Thinking Dataset for Telecom Fraud Detection*, 2025 ([arXiv:2503.24115](https://arxiv.org/abs/2503.24115)) | ASR + reasoning LLM pipelines are competitive; structured JSON verdicts; privacy-preserving synthetic data via TTS |
| *TeleAntiFraud 2.0*, 2026 ([arXiv:2609.18748](https://arxiv.org/abs/2609.18748)) | Evaluate against lawful near-domain calls; report balanced metrics, not fraud F1 alone |
| Lee et al., *Vishing-Tactics-Bench: Forecasting Exploitation Trajectories in Voice Phishing Calls*, Findings of EMNLP 2026 ([arXiv:2609.07151](https://arxiv.org/abs/2609.07151)) | Track scam tactics over time and forecast harm early, under a false-alarm budget |
| Chang and Danescu-Niculescu-Mizil, *Trouble on the Horizon*, EMNLP 2019 ([D19-1481](https://aclanthology.org/D19-1481/)) | Forecasting where a conversation is heading before the harmful turn |
| Stajano and Wilson, *Understanding Scam Victims: Seven Principles for Systems Security*, CACM 2011 ([tech report](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-754.html)) | Psychological basis for the red-flag taxonomy |
| Wang et al., *MASK: Modular Adaptive Sanitization Kit for Privacy-Preserving Phone Scam Detection*, 2025 ([arXiv:2510.18493](https://arxiv.org/abs/2510.18493)) | Sanitise transcripts before LLM reasoning |
| Li et al., *Talking Like a Phisher: LLM-Based Attacks on Voice Phishing Classifiers*, EAI ICDF2C 2025 ([arXiv:2507.16291](https://arxiv.org/abs/2507.16291)) | Test against LLM-paraphrased scam scripts |
| Iwamoto et al., *How Bad Are Artifacts?: Analyzing the Impact of Speech Enhancement Errors on ASR*, Interspeech 2022 ([arXiv:2201.06685](https://arxiv.org/abs/2201.06685)) | Don't put a denoiser in front of the speech recogniser |
| Snyder et al., *MUSAN: A Music, Speech, and Noise Corpus*, 2015 ([arXiv:1510.08484](https://arxiv.org/abs/1510.08484)) | Standard noise source for robustness testing |
| Wang et al., *Self-Consistency Improves Chain of Thought Reasoning in Language Models*, ICLR 2023 ([arXiv:2203.11171](https://arxiv.org/abs/2203.11171)) | Sample Evon several times for borderline verdicts before a hard warning |

---

## Project status and roadmap

- [x] Gnani API access verified: Timbre v2.5 synthesis and Prisma v2.5 transcription (`scripts/smoke_test.py`)
- [x] Prisma v2.5 streaming client from file or microphone, with partial transcripts about every 450 ms
- [x] Red-flag lexicon: Hindi (Devanagari and Hinglish), English, draft Tamil and Bengali; OTP and ID masking
- [x] Evon v3.3 client: structured verdicts, evidence guard, majority vote; Kaggle notebook to host it for free
- [x] Risk scorer with escalation ladder; spoken warnings with Timbre v2.5 (cached)
- [x] End-to-end pipeline, Telegram family alerts, live dashboard
- [x] Voice-cloned warnings (with consent)
- [x] Evaluation pipeline with telephone and noise simulation; first results below
- [x] Exotel adapter for merge-in mode (written to the documented protocol, waiting for account access)
- [x] Evon hosted on Kaggle, tuned and evaluated (audio: 9/9 scams with hard warnings, 0/9 false alarms)
- [x] Larger evaluation set: 18 hand-written calls (Evon-written scripts were tried and were not usable)
- [ ] Human-recorded calls, recorded noise, Tamil and Bengali calls
- [ ] Warn faster (now 12 to 16 s after the first red flag)
- [ ] Post-call debrief and 1930 report draft

**Later:** carrier-level integration, an on-device model for phones without a companion device, all ten Prisma languages, voice-deepfake detection, and a "scam drill" mode that lets families practise with simulated calls.

### Results so far (October 11 to 12, 2026)

18 synthetic Hindi calls written for this project: 9 scams (digital arrest, FedEx/police, bank KYC, a KYC scam reworded to avoid every keyword, UPI refund, electricity cut, relative in trouble, KBC lottery, task job) and 9 genuine look-alikes (delivery OTP, a real bank fraud alert, a son asking for fees, a real family emergency, passport police verification, electricity reminder, insurance renewal, job interview, loan offer). Voiced with Timbre v2.5, passed through a simulated phone line (8 kHz, 300 to 3,400 Hz, G.711), streamed through Prisma v2.5, judged by keywords plus a self-hosted Evon v3.3.

**Audio, keywords + Evon** ([eval/REPORT.md](eval/REPORT.md)):

| Condition | Scams warned | Hard warning | False alarms | Prisma character error rate |
|---|---|---|---|---|
| Phone line | 9 of 9 | 9 of 9 | 0 of 9 | 5.3% |
| Phone line, noise at 5 dB | 9 of 9 | 9 of 9 | 0 of 9 | 5.4% |

**Text, turn by turn: what Evon adds** ([eval/TEXT_EVAL.md](eval/TEXT_EVAL.md)):

| | Keywords only | Keywords + Evon |
|---|---|---|
| Scams warned | 4 of 9 | 8 of 9 |
| False alarms | 0 of 9 | 0 of 9 |

Keywords alone miss scams that avoid typical words (UPI refund, task job, a reworded KYC scam); Evon catches them from meaning and also warns earlier (digital arrest at turn 3 instead of turn 8).

Caveats: small and synthetic, all Hindi, and two Evon rules were added after seeing misses on these calls, so the numbers are optimistic until confirmed on fresh calls. The median warning comes 12 to 16 seconds after the first red flag, which is the next thing to improve. Earlier keyword-only runs down to 0 dB SNR are in the git history of `eval/REPORT.md`.

## Running it

Requires Python 3.10+, ffmpeg, and a Gnani AI API key with speech-to-text and text-to-speech access. Copy `.env.example` to `.env` and fill in what you have.

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt          # Windows (use .venv/bin/pip on Linux/macOS)
.venv/Scripts/python scripts/smoke_test.py             # Timbre speaks a line, Prisma transcribes it
```

| What | Command |
|---|---|
| Live transcription | `python scripts/transcribe_stream.py --mic` or `--file call.wav --rate 8000` |
| Make a test call from a script | `python scripts/synth_call.py eval/calls/hi_digital_arrest_01.yml` |
| Kavach on a recorded call | `python scripts/run_kavach.py --file cache/calls/hi_digital_arrest_01.wav --rate 8000` |
| Guardian mode (speakerphone) | `python scripts/run_kavach.py --mic --speaker local --evon` |
| Live dashboard | `python -m kavach.web.app`, then open http://localhost:8765 (press `f` for film mode) |
| Evaluation | `python scripts/run_eval.py --conditions phone,phone_snr10,phone_snr5,phone_snr0` |
| Pre-generate warnings | `python scripts/prebuild_warnings.py --lang hi-IN` |
| Clone a family voice (with consent) | `python scripts/clone_voice.py --name son --audio son.wav --consent` |
| Check a hosted Evon | `python scripts/evon_check.py` |
| Tests | `python -m pytest -q tests` |

Hosting Evon: [docs/EVON_HOSTING.md](docs/EVON_HOSTING.md) (free on Kaggle with `deploy/kaggle_evon.ipynb`). Merge-in mode: [docs/EXOTEL_SETUP.md](docs/EXOTEL_SETUP.md).

### Notes on Gnani's APIs from building this

- Prisma's streaming endpoint accepts an undocumented `x-partials: true` header and then sends `partial_transcript` events about every 450 ms. Kavach scans partials, so it can react mid-sentence.
- Prisma's `connected` event always reports a 16 kHz sample rate, whatever `x-sample-rate` says, so Kavach always streams 16 kHz and simulates telephone bandwidth locally.
- Prisma sometimes spaces out acronyms ("सी बी आई"), so the lexicon matches spaced and joined forms.

## Project layout

```
kavach/
  audio/       file and microphone sources, frame rechunking
  stt/         Prisma v2.5 streaming client
  detect/      normalisation and masking, keyword lexicons, Evon client, risk scorer
  speak/       Timbre v2.5 and voice cloning, warning texts, playback
  alerts/      Telegram family alerts
  telephony/   Exotel AgentStream adapter
  eval/        telephone and noise simulation, evaluation runner
  web/         dashboard server and page
  pipeline.py  one Kavach session, end to end
scripts/       command-line tools listed above
eval/calls/    synthetic call scripts (fictional names and numbers)
deploy/        Kaggle notebook for Evon
docs/          research notes, hosting and telephony guides
```

## Limitations

- Evaluated on synthetic and staged calls, not on real victims.
- Guardian mode needs the call on speakerphone and a second device nearby.
- Both speakers arrive on one audio channel, so who said what is inferred from content, not separated acoustically.
- Detection uses words only. Tone and pauses, which also signal fraud, are not used yet.
- Languages beyond Hindi, Hinglish, Tamil and Bengali are less tested.

## Acknowledgements

Built on [Gnani AI](https://www.gnani.ai)'s Prisma, Timbre and Evon models for the Great Indian AI Internship Challenge 2026. #GnaniAI #GreatIndianAIInternshipChallenge
