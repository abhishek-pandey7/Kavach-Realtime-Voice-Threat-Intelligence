# Kavach: Realtime Voice Threat Intelligence

**Kavach listens to a phone call as it happens, recognises scam scripts in Indian languages, and speaks a warning into the call before any money moves.**

Built for Gnani AI's [Great Indian AI Internship Challenge](https://www.gnani.ai/internship) ("Build Sovereign AI for India"), entirely on Gnani AI's own speech and language models.

> Status: in active development (October 2026). All data used in this project is synthetic or staged with consent. See [Data and privacy](#data-and-privacy).

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

- [x] Gnani API access verified: Timbre v2.5 synthesis and Prisma v2.5 transcription working (`scripts/smoke_test.py`)
- [ ] Live microphone to Prisma streaming client
- [ ] Red-flag lexicon (Hindi, Hinglish, English, Tamil, Bengali)
- [ ] Self-hosted Evon v3.3 returning structured verdicts
- [ ] Risk scorer, escalation ladder and spoken warnings
- [ ] Family alerts and live dashboard
- [ ] Voice-cloned warnings (with consent)
- [ ] Evaluation pipeline and report
- [ ] Merge-in mode over telephony

**Later:** carrier-level integration, an on-device model for phones without a companion device, all ten Prisma languages, voice-deepfake detection, and a "scam drill" mode that lets families practise with simulated calls.

## Setup

Requires Python 3.10+ and a Gnani AI API key with speech-to-text and text-to-speech access.

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt     # Windows (use .venv/bin/pip on Linux/macOS)
echo GNANI_API_KEY=your_key_here > .env
.venv/Scripts/python scripts/smoke_test.py        # Timbre speaks a test line, Prisma transcribes it
```

## Limitations

- Evaluated on synthetic and staged calls, not on real victims.
- Guardian mode needs the call on speakerphone and a second device nearby.
- Both speakers arrive on one audio channel, so who said what is inferred from content, not separated acoustically.
- Detection uses words only. Tone and pauses, which also signal fraud, are not used yet.
- Languages beyond Hindi, Hinglish, Tamil and Bengali are less tested.

## Acknowledgements

Built on [Gnani AI](https://www.gnani.ai)'s Prisma, Timbre and Evon models for the Great Indian AI Internship Challenge 2026. #GnaniAI #GreatIndianAIInternshipChallenge
