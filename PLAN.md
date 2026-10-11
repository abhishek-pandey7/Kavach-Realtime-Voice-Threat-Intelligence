# Kavach — Project Plan

**Live scam-call shield in Indian languages, built on Gnani AI's Prisma, Evon and Timbre.**

| | |
|---|---|
| Hackathon | The Great Indian AI Internship Challenge — "Build Sovereign AI for India" (Gnani AI) |
| Deadline | **Nov 10, 2026, 11:59 PM IST** (fixed, no extensions). Our target: submit **Nov 9**. |
| Plan written | Oct 11, 2026 (30 days left) |
| Owner | Abhishek Pandey |
| Official sources | [Challenge page](https://www.gnani.ai/internship) · [Challenge blog](https://www.gnani.ai/resources/blogs/great-indian-ai-internship-challenge-2026) · [Registration form](https://www.gnani.ai/great-indian-ai-internship-registration-form) · [Gnani docs](https://docs.gnani.ai/llms.txt) · [Evon on Hugging Face](https://huggingface.co/gnani/gnani-evon-v3.3-30b-a3b) |

---

## 0. How to use this document

1. **Section 1 is the source of truth.** It restates what the hackathon asks for, quoted from the official page. If anything else in this plan conflicts with Section 1, Section 1 wins.
2. **Section 2 (Requirement Traceability Matrix)** maps every hackathon requirement to the exact thing we build or produce. Before starting any task, check which requirement it serves. If it serves none, it's scope creep.
3. **Section 3 (Guardrails)** lists what we must and must not do.
4. Every task in the timeline (Section 14) carries requirement IDs like `[R3]`, so we can always see why we're doing it.
5. Update the **Status Log (Section 19)** whenever something changes.

---

## 1. Hackathon reference (source of truth)

### 1.1 What the hackathon is
> "The Great Indian AI Internship Challenge. Build Sovereign AI for India. Build on Gnani AI's own models and compete for paid internships."

- **Brief is open:** "There's no set problem statement. Build any working application on Gnani AI's models or APIs."
- **A finished entry is:** "a working application built on at least one Gnani AI model or API, shown working in a public video."

### 1.2 What's on offer
| Prize | Detail |
|---|---|
| Internships | Up to **100** paid six-month internships, starting **Jan 1, 2027** |
| Stipend | **Up to ₹1 lakh per intern per month**: a ceiling, individual, never split between teammates |
| Awards | **10 awards × ₹50,000** (₹5 lakh total). Judged on each category's criteria, **independent of internship selection**. **No individual or team can win more than one award.** |

### 1.3 Eligibility (all three must be true on the day you register)
- ✓ Currently enrolled in a degree or course at a college or university in India
- ✓ 18 or older
- ✓ Solo, or with exactly one teammate who also meets these conditions

Teams: the primary registrant adds the teammate's email; the teammate accepts terms independently; **all contest communication goes to the primary registrant**; each member is interviewed and considered **individually**.

### 1.4 Models we may build on
| Model | Type | Key facts (official) | Access |
|---|---|---|---|
| **Prisma v2.5** | Speech to text | Trained on 14M+ hours of telephonic audio; streams in under 200 ms; 10+ Indian languages plus Hinglish, Tanglish, Benglish | API (REST + WebSocket) |
| **Timbre v2.5** (Beta) | Text to speech | 10+ Indic languages, context-aware prosody, Indian names, numerals, lakh/crore cadence; streams over WebSocket and SSE | API |
| **Evon v3.3** | Reasoning LLM, open weight | 30B-parameter MoE (~3.5B active), 128K context, 11 Indian languages, Apache 2.0 | **Not on the API.** Weights on Hugging Face; self-host |
| Voice cloning | Part of the TTS platform | Clone embeddings → cloned TTS (REST/SSE/WebSocket) | API (docs: `/api/VC/…`) |

> The challenge blog recommends combining models, e.g. **Prisma + Evon + Timbre** for a full voice pipeline. That's exactly our design.

### 1.5 The six rules that matter most (quoted, with what they mean for us)
| # | Official rule | Implication for Kavach |
|---|---|---|
| 1 | "Offers and stipends are individual." | If we become a duo, both members must be able to explain the whole system in an interview. |
| 2 | "The brief is open." | Our problem choice (live scam calls) is allowed. No need to fit a template. |
| 3 | "Your project uses Gnani AI technology. Your submission names the Gnani AI models or APIs it uses and each member's contribution." | Gnani models must be **central**, not decorative. We name all three and log who did what. |
| 4 | "You demo it in public. Post your project on LinkedIn or X with the hashtags #GnaniAI and #GreatIndianAIInternshipChallenge, then nominate those posts in your submission. **The post has to be live before you submit.**" | Post by ~Oct 30, well before Nov 9 submit. |
| 5 | "The deadline is fixed. Final submissions close at 11:59 PM IST on November 10, 2026. You can edit project details until you submit." | Submit Nov 9. Don't click final submit until everything is ready. |
| 6 | "Keep it authentic. Bought engagement, bots, paid promotion, engagement swaps, plagiarism and misleading demos aren't allowed." | No fake demos, no engagement pods, label reenactments. |

Additional from the blog:
- **Use synthetic data only.** No real phone numbers, account numbers, Aadhaar, PAN or recorded calls. Voice data is personal data under India's DPDP Act.
- **"An honest limitation is better than a faked result."**

### 1.6 The four steps (and every field they ask for)
**Step 1 — Register:** full name, email, phone · college, degree/course, discipline · year of study, graduation year, city · solo or team + teammate email. Each teammate accepts the contest terms.

**Step 2 — Build (project details, editable until submission):**
- Project title
- The problem you are solving
- Who will use it
- The Gnani AI models or APIs you use
- Each member's contribution

**Step 3 — Post your demo:**
- Record a video of your application working
- Post it on LinkedIn, X or both
- Explain what you built and the Gnani AI technology used
- **Tag Gnani AI** and add **#GreatIndianAIInternshipChallenge** and **#GnaniAI**
- "Tagging alone doesn't complete your entry. You nominate the post in step 4."

**Step 4 — Submit:**
- Your demo video
- A written project explanation
- The Gnani AI models or APIs you used
- **One nominated post link per platform**
- By 11:59 PM IST, Nov 10, 2026

### 1.7 Selection process (how internships are decided)
| Stage | Official description | What we optimise |
|---|---|---|
| 01 Engagement check | "Gnani AI verifies reactions, comments and reshares on your nominated posts, recorded by the closing cutoff." | **Genuine** reactions/comments/reshares on the nominated posts, accumulated before Nov 10. |
| 02 Eligibility check | "Entries must show genuine use of Gnani AI technology and meet the participation requirements." | Gnani models visibly at the core of the pipeline. |
| 03 Shortlisting | "The eligible projects with the strongest verified engagement are shortlisted for interview." | Engagement again: the post is the most important deliverable after the working app. |
| 04 Interviews | "Every shortlisted person interviews on their own, including both members of a team." | Deep understanding of our own system (Section 18). |
| 05 Written offers | "Offers and stipends depend on each candidate's assessed skills, interview performance and fit for available roles." | Skills shown in the repo, eval and interview. |

> **Key insight:** the post's engagement gets you to the interview; technical depth gets you the offer. We need both.

### 1.8 Awards (official criteria)
| # | Award | Official criterion |
|---|---|---|
| 01 | Main Character | Best build in a regional or low-resource Indian language |
| 02 | Mixed Vibes | Best code-mixed voice experience across Hinglish, Tanglish and Benglish |
| 03 | **Real Deal** | Most useful real-world problem solved, for users such as farmers, kirana stores or rural health workers |
| 04 | **Noise Canceller** | The build that performs best on messy, noisy, real telephonic audio |
| 05 | Two-Person Army | Best project by a team of two |
| 06 | Solo Ninja | Best project by a single participant |
| 07 | **Jugaad Genius** | Most creative or unexpected use of Gnani AI's models |
| 08 | Small Town, Big Build | Best entry from a Tier 2 or Tier 3 college or city |
| 09 | **Demo Day Drop** | Best 60-second demo video |
| 10 | Crowd Favourite | Public votes on LinkedIn and X using #GreatIndianAIInternshipChallenge & #GnaniAI. Purchased votes, bots and engagement exchanges don't count. |

### 1.9 Build resources
- **5,000 programme credits** per registration (for teams, on the primary registrant's account). Access instructions by email after sign-up.
- API dashboard (keys, voices, usage): https://app.gnani.ai/voice/
- Docs + quick start: https://docs.gnani.ai
- Evon on Hugging Face (open weights, Apache 2.0)
- **Support on Discord** (build questions, Gnani team)

### 1.10 Open FAQ topics to check on the registration page / Discord
The page lists these FAQs, but the answers weren't in our source. **Read them before building further:** "Can I use the agent builder? Why can't I find API keys for it?", "How do I use Evon?", "Is there a participant workspace?", "Where do I build?", "How is my data handled?", plus the full **programme terms** (IP ownership, data handling).

---

## 2. Requirement Traceability Matrix

| ID | Requirement (source) | How Kavach satisfies it | Evidence we'll produce | Status |
|---|---|---|---|---|
| R1 | Eligible: enrolled in Indian college, 18+, solo/duo (§1.3) | Abhishek registers as primary | Registration confirmation email | ☐ |
| R2 | Working application (§1.1) | Mode A end-to-end runs live; Mode B if Exotel allows | Unedited live take, public repo | ☐ |
| R3 | Built on ≥1 Gnani model; genuine use (§1.1, §1.7-02) | **All three** on the critical path: Prisma hears, Evon decides, Timbre speaks (+ voice cloning) | Architecture diagram, code, README "Gnani models used" section | ☐ |
| R4 | Name the Gnani models/APIs used (Rule 3, Step 2, Step 4) | Prisma v2.5 streaming STT · Evon v3.3 (self-hosted) · Timbre v2.5 TTS + voice cloning API | Submission form text (§13) | ☐ |
| R5 | Each member's contribution (Rule 3, Step 2) | Contribution log kept in this doc (§15) | Submission form text | ☐ |
| R6 | Project title, problem, users (Step 2) | Drafted in §5 | Submission form text | ☐ |
| R7 | Video of the app working (Step 3, Step 4) | 60 s demo + 2–3 min walkthrough + raw take | Video files | ☐ |
| R8 | Public post on LinkedIn and/or X explaining what we built + Gnani tech (Step 3) | Post copy drafted in §12 | Live post URLs | ☐ |
| R9 | Tag Gnani AI + #GnaniAI + #GreatIndianAIInternshipChallenge (Rule 4, Step 3) | In both posts; checklist in §12 | Screenshot of posts | ☐ |
| R10 | Post live **before** submitting (Rule 4) | Post Oct 28–30; submit Nov 9 | Post timestamps | ☐ |
| R11 | One nominated post link per platform (Step 4) | Nominate the main LinkedIn post + main X post | Submission form | ☐ |
| R12 | Written project explanation (Step 4) | Drafted in §13 | Submission form | ☐ |
| R13 | Deadline Nov 10, 11:59 PM IST (Rule 5) | Internal deadline Nov 9 | Submission confirmation | ☐ |
| R14 | Authentic: no bought engagement, bots, swaps, plagiarism, misleading demos (Rule 6) | Guardrails §3; "staged reenactment" label; raw take linked; own code | Raw take link, repo history | ☐ |
| R15 | Synthetic data only; DPDP (blog) | Synthetic scripts + TTS audio + consenting actors; no real PII | Data section in README (§9) | ☐ |
| R16 | Engagement verified by closing cutoff (§1.7-01) | Early post, genuine sharing plan (§12) | Engagement on nominated posts | ☐ |
| R17 | Interview readiness, individual (§1.7-04/05) | Interview prep (§18), deep ownership of code | — | ☐ |
| A3 | Real Deal: most useful real-world problem | Protects elderly/non-English users from live scam calls | Problem stats (cited), user story | ☐ |
| A4 | Noise Canceller: messy, noisy, real telephonic audio | 8 kHz + noise eval, speakerphone re-capture, Mode B real phone line | `eval/REPORT.md` | ☐ |
| A7 | Jugaad Genius: unexpected use of models | Cloned family voice warns into the call; Evon writes + Timbre voices our own eval set | Demo moment + eval pipeline | ☐ |
| A9 | Demo Day Drop: best 60 s video | Storyboard §11 | 60 s video | ☐ |
| A10 | Crowd Favourite: public votes | Genuinely useful message people forward to their parents | Engagement | ☐ |

---

## 3. Guardrails: staying inside what the hackathon wants

### Must do
- ✅ Keep **Gnani models on the critical path.** Every detection must flow through Prisma; every spoken output through Timbre; the reasoning through Evon. [R3]
- ✅ Name the models exactly: "Prisma v2.5", "Timbre v2.5", "Evon v3.3", "Gnani voice cloning API". [R4]
- ✅ Show the app **actually working** in the video. The system must run live during filming. [R2, R7, R14]
- ✅ Label reenactments: "Staged reenactment · synthetic data". [R14, R15]
- ✅ Post live before submitting; nominate one post per platform. [R10, R11]
- ✅ Keep a contribution log, even if solo. [R5]
- ✅ State limitations honestly in the post, README and submission. [R14]

### Must not do
- ❌ **No non-Gnani STT, TTS or LLM in the product path** (no Whisper, OpenAI, Gemini, ElevenLabs, Sarvam, etc.). Using them would weaken "genuine use of Gnani AI technology" [R3]. *Exception:* other models may appear **only in the evaluation as comparison baselines**, clearly labelled.
- ❌ No real scam recordings, real phone numbers, Aadhaar, PAN or account numbers, anywhere: code, eval set, video, screenshots. [R15]
- ❌ No cloning anyone's voice without their recorded consent. No celebrity or official voices. [R14, R15]
- ❌ No edited/faked transcripts or pre-recorded "AI responses" passed off as live. [R14]
- ❌ No engagement pods, like-for-like swaps, paid promotion, bots or bought engagement. [R14, A10]
- ❌ No KYC on Exotel under the internship company's name. [Ethics]
- ❌ Don't let stretch features (Scam Drill, extra languages) delay the posting date. [R10, R16]

### Scope fence
| In scope (v1) | Out of scope (mention as "next steps" only) |
|---|---|
| Live detection during a call (Mode A, Mode B if available) | Carrier/telecom-level integration |
| Hindi, Hinglish, Tamil, Bengali (+ Kannada/Marathi if time) | All 10 languages fully tuned |
| Spoken warning (Timbre + cloned voice), Telegram family alert | Native Android app with call-screen overlay |
| Dashboard for demo + post-call debrief | Accounts, billing, multi-family management |
| Synthetic eval with honest numbers | Real-world pilot with real users |

---

## 4. Award strategy

**Rule:** a team can win only one award, so we build one strong project that's eligible for several and let judges pick.

| Priority | Award | Why we fit | What we must show |
|---|---|---|---|
| 1 | **Real Deal** (A3) | Live scam calls are a real, widespread harm; our users are elderly and non-English households, close to the "rural health workers / kirana" type of users named in the criterion | Clear user story, cited problem stats, working demo, family alert |
| 2 | **Noise Canceller** (A4) | Our input *is* telephonic audio, often re-captured on speaker in noisy homes | Numbers across noise levels and 8 kHz codec; live Mode B on a real phone line if possible |
| 3 | **Jugaad Genius** (A7) | Cloned family voice speaking into the scam call; Gnani models generating their own test set | Cloned-voice moment in demo; eval pipeline described |
| 4 | **Demo Day Drop** (A9) | Storyboard built around a tense, relatable 60 s story | Polished 60 s video |
| 5 | **Crowd Favourite** (A10) | Message is useful to share ("send this to your parents") | Honest engagement |
| — | Solo Ninja / Two-Person Army | Depends on team decision (§15) | — |
| — | Small Town, Big Build | Only if college/city is Tier 2/3. **To confirm.** | — |
| — | Mixed Vibes / Main Character | Partial fit (Hinglish, Tamil, Bengali), but other entries will centre on language | Language coverage as a bonus |

---

## 5. Project definition (Step 2 fields, draft answers) [R6]

**Project title:** Kavach: AI that joins the call and stops the scam

**The problem you are solving:**
Phone scams such as fake "digital arrest" calls, fake KYC and courier/customs threats keep victims on the line for long periods, cut them off from family ("kisi ko mat batana") and pressure them into paying while still on the call. Elderly and non-English-speaking people are hit hardest. Caller-ID spam labels fail when scammers use fresh numbers, and advice after the call comes too late. Kavach listens to *what is being said* during the call, recognises scam patterns in Indian languages in real time, and warns the person, out loud and in their own language, before money moves.

*(Add 2–3 cited public statistics from I4C / NCRB / RBI / reputable news before submitting. Do not invent numbers.)*

**Who will use it:**
Families with elderly parents, especially in non-English and Tier 2/3 households. The family sets up Kavach once (an old Android phone near the parents, or a phone number they can merge into a call), and the parents are protected during calls in Hindi, Hinglish, Tamil, Bengali and more.

**Gnani AI models/APIs used:**
- **Prisma v2.5** (streaming speech-to-text, WebSocket): transcribes noisy, code-mixed call audio in real time
- **Evon v3.3** (open-weight reasoning model, self-hosted): reads the live transcript and decides if it's a scam, which type, which red flags, and what to say
- **Timbre v2.5** (text-to-speech, WebSocket): speaks the warning into the call in the listener's language
- **Gnani voice cloning API**: speaks the warning in a consenting family member's voice
- Also used in evaluation: Evon writes synthetic call scripts and Timbre voices them

**Each member's contribution:** see §15.

---

## 6. Product specification

### 6.1 Modes
**Mode A — Kavach Guardian (P0, primary demo)** [R2]
- A spare Android phone, tablet or laptop near the parents runs Kavach (web app / PWA, or Python client).
- When a call is on speakerphone, Guardian hears both sides through its mic.
- Warnings play from Guardian's speaker. The parent hears them, **and so does the scammer** through the parent's phone mic.
- Why this design: Android blocks other apps from using the mic during a call, so a second device is the realistic way to listen without telecom access. Most families have an old phone.

**Mode B — Merge-in Kavach (P1, stretch)** [R2, A4]
- Parent taps "Bulao Kavach" → server calls Exotel `Calls/connect` (`StreamType=bidirectional`) to the parent's verified number → parent merges it into the scam call.
- Kavach receives real 8 kHz telephone audio and plays warnings directly into the call.
- Depends on Exotel enabling AgentStream on SID `elyratechnologies1` (ticket `DCA20261010853508`). **Go/no-go: Oct 20.**

### 6.2 Features by priority
| ID | Feature | Priority | Serves |
|---|---|---|---|
| F1 | Streaming transcription from mic via Prisma WS | P0 | R2, R3 |
| F2 | L1 multilingual red-flag keyword detector | P0 | R2 |
| F3 | L2 Evon scam reasoning (JSON verdict) | P0 | R3 |
| F4 | Risk scorer + escalation ladder | P0 | R2 |
| F5 | Spoken warning via Timbre in caller's language | P0 | R3 |
| F6 | Live dashboard (transcript, risk meter, red-flag chips, timer) | P0 | R7, A9 |
| F7 | Family alert via Telegram (summary + red flags) | P0 | A3 |
| F8 | Cloned family-voice warning (with consent) | P1 | A7, A9 |
| F9 | Mode B via Exotel | P1 | A4 |
| F10 | Post-call debrief in parent's language + 1930 / cybercrime.gov.in report draft | P1 | A3 |
| F11 | Synthetic eval pipeline + report | P0 | A4, R17 |
| F12 | Scam Drill: simulated practice call + debrief (family consent) | P2 | A7 |
| F13 | Kannada / Marathi / Telugu support | P2 | A1 bonus |

**Rule:** P0 done by Oct 21; P1 by Oct 27; P2 only after the post is live.

### 6.3 User story (for the video and post)
1. Mom gets a call: "This is CBI. A parcel in your name has drugs. You are under digital arrest. Don't tell anyone."
2. She puts it on speaker (or taps "Bulao Kavach").
3. Within seconds the dashboard shows: *Fake authority → Threat of arrest → Secrecy → Payment demand.*
4. Kavach speaks, in her son's voice: "Maa, main hoon. Police phone pe arrest nahi karti. Ye call kaat do."
5. The scammer hears "this call is being monitored" and hangs up.
6. The son gets a Telegram alert with a summary. Mom gets a short debrief in Hindi.

---

## 7. Architecture and how each Gnani model is used [R3, R4]

```
            ┌───────────────── Audio source (pluggable) ─────────────────┐
            │  Mode A: mic (browser/PWA or Python)                        │
            │  Mode B: Exotel bidirectional WebSocket (8 kHz PCM, ~100ms) │
            └──────────────────────────────┬──────────────────────────────┘
                                           │ resample + re-chunk → 1024-byte frames
                                           ▼
          ① PRISMA v2.5 streaming STT   wss://api.vachana.ai/stt/v3/stream
                                           │ segment transcripts (+ language)
                                           ▼
                ┌──────────── Detection engine ─────────────┐
                │ L1: keyword/regex red flags (instant)      │
                │ ② EVON v3.3 (self-hosted) on rolling       │
                │    60 s window → JSON verdict              │
                │ Risk scorer: fusion + hysteresis + ladder  │
                └──────────────┬──────────────────┬──────────┘
                               ▼                  ▼
     ③ TIMBRE v2.5 TTS / ④ VOICE CLONE      Alerts + UI
       wss://api.vachana.ai/api/v1/tts      - Telegram to family
       → speaker (Mode A) or call (Mode B)  - Live dashboard (WS)
                                            - Post-call debrief (Evon) + 1930 draft
```

### 7.1 Gnani model usage table
| Gnani component | Where | What it does | Config (from docs) |
|---|---|---|---|
| ① Prisma v2.5 (WebSocket) | Every call, continuously | Turns call audio into text, incl. code-mixed | PCM16 mono; `x-sample-rate` 8000 (Mode B) / 16000 (Mode A); exactly 1024-byte frames at real-time pace; header `x-api-key-id`; tune `x-min-silence-ms` (~300) and `x-max-speech-s`; 15-min session cap → reconnect; langs: hi/en/ta/bn/kn/mr/te/ml/gu/pa-IN |
| ② Evon v3.3 (self-hosted) | Every new segment | Scam verdict, type, red flags, warning text; post-call debrief; eval script generation | vLLM ≥0.12 OpenAI-compatible endpoint or 4-bit GGUF via llama.cpp; temp 0.6, top_p 0.95; thinking **off** for live verdicts |
| ③ Timbre v2.5 (WebSocket) | On warnings, debrief | Speaks warning in the right language | model `timbre-v2.5`; Mode B: 8 kHz `linear_pcm`/`mulaw`; Mode A: 16–24 kHz; write numbers as words |
| ④ Voice cloning API | Hard warnings (P1) | Same warning in family member's voice | Clone embedding created once from consented sample |
| Prisma REST / batch | Evaluation | Transcribe the eval set cheaply | REST for ≤60 s clips; batch API for the full set |

### 7.2 Non-Gnani parts (supporting only)
| Part | Tool | Why it's OK |
|---|---|---|
| Telephony | Exotel AgentStream | Just carries audio; no AI |
| Family alert | Telegram Bot API | Notification channel |
| Dashboard | Vite + vanilla JS/React | UI |
| Tunnel | ngrok / cloudflared | Networking |
| Evon hosting | Rented GPU / Kaggle / local | Compute for a Gnani model |

### 7.3 Repo layout
```
kavach/
  server/
    main.py              # FastAPI app, WS endpoints, orchestration
    config.py            # loads .env
    audio/               # mic.py, exotel.py, rechunk.py, resample.py
    stt/prisma.py        # streaming client + reconnect
    detect/
      lexicon/           # hi.yml, en.yml, ta.yml, bn.yml red-flag phrases
      keywords.py        # L1
      evon.py            # L2 prompt, JSON parse, timeout/fallback
      scorer.py          # fusion, hysteresis, escalation ladder
    speak/timbre.py      # TTS + cloned voice, routing to speaker/call
    alerts/telegram.py
    debrief.py           # post-call summary + 1930 draft
  dashboard/             # live UI built for filming
  eval/
    gen_scripts.py       # Evon writes scam + benign scripts
    synth_audio.py       # Timbre voices them
    degrade.py           # noise mix + 8 kHz G.711
    run_eval.py          # metrics → REPORT.md
  docs/architecture.png
  README.md              # incl. "Gnani models used", data & privacy, limitations
  .env                   # GNANI_API_KEY, EVON_URL, EXOTEL_*, TELEGRAM_* (gitignored)
```

---

## 8. Detection design

### 8.1 Scam taxonomy (v1)
| Type | Red flags (examples, multilingual lexicon to be built) |
|---|---|
| Digital arrest / fake police, CBI, ED, TRAI | "case registered", "arrest warrant", "video call pe raho", "kisi ko mat batana", "verification ke liye paise" |
| Courier / customs | "aapke naam pe parcel", "drugs / fake passports mile", "customs" |
| Bank / KYC / card block | "KYC expire", "account freeze", "OTP batao", "AnyDesk / app download karo" |
| UPI refund / collect | "galti se paise bhej diye", "PIN daalo receive karne ke liye" |
| Relative in trouble | "aapka beta police station / accident", urgent money |
| Utility disconnection | "aaj raat bijli kat jayegi", "is number pe call karo" |
| Prize / job / task | "registration fee", "advance payment", "prize claim" |

Red-flag categories: `fake_authority`, `threat`, `secrecy`, `urgency`, `payment_demand`, `credential_request` (OTP/PIN), `remote_access`, `isolation`.

### 8.2 Layers
- **L1 (instant):** phrase lexicon per language → flags with weights. Explainable; catches obvious scripts before Evon replies.
- **L2 (Evon):** runs per new segment on a rolling ~60 s window. Output schema:
  ```json
  {"risk": 0, "scam_type": "none|digital_arrest|courier|kyc|upi|relative|utility|prize",
   "red_flags": [], "evidence": ["quoted phrase"], "victim_language": "hi-IN",
   "warning_soft": "...", "warning_hard": "..."}
  ```
  Prompt covers: taxonomy, red-flag definitions, inferring caller vs receiver from mixed mono audio, staying low on genuine bank/delivery calls, short output.
- **Fallback:** if Evon times out (>3 s), L1 alone can trigger a soft warning; hard warning needs Evon.

### 8.3 Escalation ladder
| Level | Trigger | Action |
|---|---|---|
| Watch | risk ≥ 40 | Dashboard amber; nothing audible |
| Soft warn | risk ≥ 65 **and** ≥2 flag types | Short spoken caution to the parent |
| Hard warn | risk ≥ 85 | "This call is being monitored by Kavach" (both sides hear) + cloned-voice warning + Telegram alert |
Same warning not repeated within 30 s.

### 8.4 Research-driven design rules (details in `docs/RESEARCH.md`)
| Rule | Source |
|---|---|
| Evon sees the whole call so far, never a single utterance | Shen et al. 2025 (arXiv:2502.03964) |
| Verdict is SAFE / UNCERTAIN / SCAM; never speak on UNCERTAIN | Shen et al. 2025 |
| Every red flag must quote evidence present in the transcript (hallucination guard) | Shen et al. 2024 (arXiv:2409.11643) |
| Evon tags tactic stage (hook, authority, threat, isolation, extraction); risk rewards progression | Vishing-Tactics-Bench 2026; Chang & Danescu-Niculescu-Mizil 2019 |
| Mask OTP/account/card/Aadhaar/phone digits as tags before Evon | MASK 2025 (arXiv:2510.18493) |
| No denoiser in front of Prisma | Iwamoto et al. 2022 (arXiv:2201.06685) |
| Borderline risk: 3 parallel Evon samples, majority vote before hard warning | Self-consistency, Wang et al. 2023 |
| Eval: near-domain hard negatives, balanced metrics, frozen set, paraphrased scam variants, MUSAN noise | TeleAntiFraud-28k / 2.0; Li et al. 2025; MUSAN |

### 8.5 Latency targets (to measure, report real numbers)
| Step | Target |
|---|---|
| End of utterance → Prisma transcript | 0.3–0.8 s |
| L1 | <10 ms |
| Evon verdict | <2 s |
| Timbre first audio | <0.7 s |
| **Red-flag phrase → warning starts** | **<4 s** |

---

## 9. Data, privacy and consent [R15, R14]

- **Synthetic only.** All call scripts are written by us or generated by Evon. All audio is Timbre-generated or recorded by consenting friends/family acting from scripts.
- **No real PII** anywhere: use obviously fake names, numbers like "nine eight seven…" from fictional scripts, no Aadhaar/PAN/account numbers.
- **Consent:** written/recorded consent from everyone on camera and from the person whose voice is cloned. Keep consent notes in a private folder (not in the repo).
- **No storage by default:** live call audio is processed in memory; transcripts kept only in demo mode.
- **Self-hosted Evon:** call transcripts don't leave our infrastructure for reasoning (sovereign AI angle).
- README section "Data & Privacy" states all of the above.

---

## 10. Evaluation [A4, R17]

### 10.1 Dataset
| Set | Size | Source |
|---|---|---|
| Scam calls | ~60 (all 7 types) | Evon-generated scripts, edited by us |
| Benign look-alikes | ~60 | Real-style bank fraud alerts, delivery calls, bill reminders, relative genuinely asking for money, insurance renewal |
| Human-recorded | ~10 | Friends acting scripts on a real phone call (speakerphone) |
| Languages | Hindi, Hinglish, Tamil, Bengali (+ Kannada/Marathi if time) | |

### 10.2 Degradation (Noise Canceller evidence)
- Background noise: traffic, pressure-cooker whistle, TV, ceiling fan, crowd, rain.
- SNR levels: clean, 20 dB, 10 dB, 5 dB.
- Telephone channel: resample to 8 kHz + G.711 μ-law.
- Speakerphone re-capture pass for Mode A realism.

### 10.3 Metrics and targets
| Metric | Target |
|---|---|
| Scam recall | ≥90% clean, ≥80% at 5 dB |
| False alarm rate (benign) | ≤5% |
| Median time-to-detect from first red flag | ≤10 s |
| Prisma WER/CER per language × noise | Report as is |

### 10.4 Ablations
L1 only vs Evon only vs both · 16 kHz clean vs 8 kHz noisy · per scam type. Optional: other STT models **as labelled baselines only**.

Output: `eval/REPORT.md` with tables + 2 charts. **Report failures honestly.**

### 10.5 Credit budget (5,000 credits)
Track usage from the dashboard daily. Use batch STT for the eval set, cache all transcripts and generated audio, never regenerate unnecessarily. *(Check per-minute/character credit costs on the dashboard on day 1.)*

---

## 11. Demo video [R7, A9]

### 11.1 Requirements checklist
- [ ] Shows the application **working** (system running live during the take)
- [ ] Explains what we built and the Gnani AI technology used (on-screen text or voiceover)
- [ ] Names Prisma v2.5, Evon v3.3, Timbre v2.5
- [ ] "Staged reenactment · synthetic data" label visible
- [ ] Exactly 60 s cut for Demo Day Drop; separate 2–3 min walkthrough for submission
- [ ] Burned-in captions (Hindi + English)
- [ ] Unedited raw take saved and linkable

### 11.2 60-second storyboard
| Time | Shot | Purpose |
|---|---|---|
| 0–3 s | Black screen: **"My mom got a call from the 'CBI'."** Phone ringing. | Hook |
| 3–14 s | Scammer (friend acting): "Aapke naam pe parcel mein drugs mile hain… digital arrest… kisi ko mat batana." Mom worried. | Tension |
| 14–18 s | Mom puts it on speaker; Guardian lights up. (Mode B: taps Bulao Kavach, merges.) | Product entry |
| 18–32 s | Split screen: live transcript, risk meter climbing, chips: Fake authority → Secrecy → Payment demand. Timer. | Proof it's live |
| 32–42 s | Son's cloned voice: "Maa, main hoon. Police phone pe arrest nahi karti. Call kaat do." Scammer: "Hello? Hello?" → hangs up. | Peak moment |
| 42–48 s | Son's phone: Telegram alert. Mom sees Hindi debrief. | Family loop |
| 48–55 s | Quick cuts: Tamil, Bengali, pressure-cooker noise take. Text with **real measured** numbers. | Range + Noise |
| 55–60 s | "Kavach · Built on Gnani Prisma + Evon + Timbre · #GnaniAI #GreatIndianAIInternshipChallenge" | Credit + tags |

Formats: 9:16 (X, reels) and 16:9 or 1:1 (LinkedIn).

### 11.3 Walkthrough (2–3 min)
Problem (cited stats) → unedited live demo → architecture + which Gnani model does what → eval results → limitations → next steps.

### 11.4 Filming checklist
- [ ] Consent from actors + voice-clone person
- [ ] Phone on stand, good light, quiet room for narration, lav mic if possible
- [ ] Evon GPU running, credits checked
- [ ] 3–4 full takes; keep best + raw
- [ ] No real numbers visible on any screen

---

## 12. Public posts [R8, R9, R10, R11, R16, A10]

### 12.1 Post requirements checklist
- [ ] Video uploaded natively (not a YouTube link)
- [ ] Explains what we built + Gnani tech used
- [ ] **Tags Gnani AI's official account**
- [ ] **#GnaniAI** and **#GreatIndianAIInternshipChallenge** both present
- [ ] "Staged reenactment, synthetic data" disclosed
- [ ] Live before submission; URLs saved for nomination
- [ ] One main post per platform (that's the one we nominate)

### 12.2 Draft: LinkedIn
> My mom's generation is the #1 target of "digital arrest" scam calls. Advice after the call is too late, so I built Kavach: an AI that listens during the call and stops the scam while it's happening.
>
> 🎥 Staged reenactment below (synthetic data, no real people's data)
>
> What it does:
> • Listens to the call in Hindi, Hinglish, Tamil, Bengali
> • Spots scam patterns like fake CBI/police, "kisi ko mat batana", payment demands
> • Warns out loud in the parent's language, in a family member's own voice, and the scammer hears it too
> • Sends the family an alert with a summary
>
> Built fully on Gnani AI's Indian models:
> 🎙 Prisma v2.5 for streaming speech-to-text on noisy phone audio
> 🧠 Evon v3.3, self-hosted, for scam reasoning
> 🔊 Timbre v2.5 + voice cloning for the spoken warning
>
> On our synthetic test set: [X]% of scams caught, [Y]% false alarms on genuine bank/delivery calls, ~[Z]s to warn. Still weak on [honest limitation].
>
> If your parents get calls like this, share it with them. 🙏
> Code: [repo link in comments]
>
> @Gnani.ai #GnaniAI #GreatIndianAIInternshipChallenge #DigitalArrest #CyberSafety #SovereignAI

*(Fill [X]/[Y]/[Z] only with real eval numbers. Use "My mom" hook only if true; otherwise "Every Indian family has heard of a 'digital arrest' call.")*

### 12.3 Draft: X
> Built an AI that joins a scam call and tells the scammer it's being watched 🛡️
>
> Kavach catches "digital arrest" & KYC scams live in Hindi/Tamil/Bengali and warns your parents in YOUR voice.
>
> Built on @[GnaniAI handle] Prisma + Evon + Timbre 🇮🇳
> (staged reenactment)
>
> #GnaniAI #GreatIndianAIInternshipChallenge

### 12.4 Genuine reach plan (no swaps, no bought engagement)
- Post weekday morning 9–11 AM IST, **Oct 28–30**.
- Share with family WhatsApp groups, college groups, coding/cyber-security clubs, professors and the college's official page (ask them to share; it's a genuinely useful public-safety message).
- Reply to every comment in the first 3 hours; answer technical questions in detail.
- Post in Gnani's Discord showcase channel if one exists.
- A follow-up "how it works" post a few days later (not nominated) to bring people back.

---

## 13. Submission package (Step 4) [R4, R7, R11, R12, R13]

| Field | Content | Ready |
|---|---|---|
| Demo video | 60 s cut + link to 2–3 min walkthrough + raw take | ☐ |
| Written project explanation | Below | ☐ |
| Gnani models/APIs used | Prisma v2.5 streaming STT (WebSocket) + REST/batch for eval; Evon v3.3 self-hosted; Timbre v2.5 TTS (WebSocket); Gnani voice cloning API | ☐ |
| Nominated LinkedIn post | URL | ☐ |
| Nominated X post | URL | ☐ |
| Project details (Step 2) | §5 | ☐ |
| Contributions | §15 | ☐ |

**Written explanation (draft outline, ~300–500 words):**
1. Problem + who it hurts (cited stats)
2. What Kavach does (user story)
3. How it works (architecture, the role of each Gnani model)
4. Results (eval table, latency)
5. Data & privacy (synthetic, consent, self-hosted Evon)
6. Limitations (honest)
7. What's next

**Final pre-submit checklist (Nov 8–9):**
- [ ] Posts are live and public (check in a logged-out browser)
- [ ] Both hashtags + Gnani tag present
- [ ] All placeholders filled with real numbers
- [ ] Repo public, README complete, no secrets committed
- [ ] Submit by **Nov 9**; save confirmation

---

## 14. Timeline (Oct 11 → Nov 10)

| Dates | Tasks | Done when | Reqs |
|---|---|---|---|
| **Oct 11–12** | Confirm challenge registration + credits. Read FAQ/terms (§1.10). Gnani key in `.env`. Test Prisma REST + WS, Timbre WS, check credit cost per call. Exotel ticket follow-up. Decide Evon hosting. | Hindi clip → transcript; text → audio | R1, R3 |
| **Oct 13–15** | Mic source → Prisma WS streaming. L1 lexicon (hi/en). Evon served and returning JSON. | Speak a scam line → flags in console <2 s | R2, R3 |
| **Oct 16–18** | Evon L2 + scorer + ladder. Timbre spoken warnings. Telegram alert. | End-to-end on speakerphone, warning spoken | R2, R3 |
| **Oct 19–21** | Dashboard. Exotel echo test → **Mode B go/no-go Oct 20**. Voice clone (consent). Tamil + Bengali lexicons. | **All P0 done** | R2, A4, A7 |
| **Oct 22–25** | Eval: scripts, synth audio, degrade, run, tune thresholds on false alarms. REPORT.md. | Real numbers in hand | A4, R17 |
| **Oct 26–27** | P1 features (debrief, 1930 draft, Mode B if go). README. Rehearse demo. | **All P1 done or cut** | A3 |
| **Oct 27–28** | Film demo + walkthrough + raw take. Edit 60 s cut. | Final videos exported | R7, A9 |
| **Oct 28–30** | **Publish LinkedIn + X posts.** Save URLs. | Posts live | R8–R10, R16 |
| **Oct 31–Nov 6** | Engage with comments. Bug fixes. P2 (Scam Drill, more languages) only if everything else is done. Follow-up post. | — | R16, A10 |
| **Nov 7–8** | Fill submission form, written explanation, contributions. Pre-submit checklist. | Draft complete | R4–R6, R11, R12 |
| **Nov 9** | **Submit.** | Confirmation saved | R13 |
| Nov 10 | Buffer only. | — | — |

---

## 15. Team and contributions [R5]

**Decision needed:** solo or duo? (affects Solo Ninja vs Two-Person Army; a teammate must also be eligible and register as your teammate.)

| Member | Role | Contributions (update as we go) |
|---|---|---|
| Abhishek Pandey | Primary registrant | Architecture, Prisma/Timbre integration, detection engine, Evon hosting, eval, demo, posts |
| (Teammate, if any) | | |

If duo, split cleanly and **both** learn the whole system for individual interviews (Rule 1).

---

## 16. Risks and fallbacks

| Risk | Impact | Fallback |
|---|---|---|
| Exotel not enabled / KYC blocked | No Mode B | Mode A is the main demo; Mode B listed as next step |
| Evon hosting too slow/expensive | Slow verdicts | 4-bit quant; shorter window; L1 handles first soft warning; rent GPU only for testing/filming |
| Credits run low | Can't test | Batch STT, caching, daily usage check; ask on Discord |
| False alarms on genuine calls | Credibility | 2+ flag types rule, tune on benign set, report the rate honestly |
| Prisma segments arrive late on long monologues | Slower detection | Lower `x-min-silence-ms`, set `x-max-speech-s` |
| Voice cloning misuse perception | Reputation | Consent shown/stated, family-only, embeddings stored locally |
| Posting slips past Oct 30 | Less engagement time | P2 never blocks posting; film by Oct 28 regardless |
| Unclear FAQ rule (e.g., agent builder, workspace) | Possible non-compliance | Read FAQ + terms on day 1; ask on Discord |

---

## 17. Things we will say in the post/README about limitations (honest)
- Evaluated on synthetic and staged calls, not real victims.
- Mode A needs the call on speaker and a second device.
- Mixed mono audio means caller/receiver separation is inferred, not certain.
- Languages beyond Hindi/Hinglish/Tamil/Bengali are less tested.
- Fill in real weaknesses found during eval.

---

## 18. Interview preparation [R17]
- Walk through the full pipeline from microphone to spoken warning, with latency numbers.
- Why streaming STT returns segments, and how silence/segment settings trade speed for accuracy.
- Mixed mono audio: how Evon infers who is the caller.
- Self-hosting Evon: hybrid Mamba-Transformer MoE, active vs total params, quantisation, memory, throughput.
- Eval design: why benign look-alikes matter, noise + codec simulation, ablation results.
- Privacy and DPDP: synthetic data, consent, no storage, self-hosting.
- What you'd build at Gnani next: carrier-level integration, on-device detection, more languages.
- Be ready to explain every line of code you wrote.

---

## 19. Status log
| Date | Update |
|---|---|
| Oct 11 | Hackathon researched; Kavach chosen. Exotel account created (SID `elyratechnologies1`); number verification failed via missed call; ticket `DCA20261010853508` raised; support (Pooja Shetty) asked for SID, sent. Plan written. |
| Oct 11 | Gnani API key created (`.env`; rotate before filming since it was pasted in chat). `scripts/smoke_test.py`: Timbre (Deepak, hi-IN, 16 kHz) → 2.7 s; Prisma REST transcribed it exactly, ~0.3 s server latency. Note: Prisma writes "CBI" as "सी बी आई" (spaced), so the L1 lexicon must normalise spaced acronyms. |
| Oct 11 (overnight build) | Built on separate branches: Prisma streaming client (found undocumented `x-partials` header: partials every ~450 ms), multilingual keyword detector with OTP/ID masking, Evon client (evidence guard, UNCERTAIN, majority vote), risk scorer and escalation ladder, Timbre warnings (10 Hindi warnings pre-generated and cached), end-to-end pipeline with echo guard and Telegram alerts, live dashboard, evaluation pipeline, Exotel adapter, Kaggle notebook for Evon. 52 tests passing. |
| Oct 11 | Evon: not on HF Inference Providers; GGUF repo is **not gated** (card is outdated). Laptop (6 GB GPU, 16 GB RAM) can't run it, so plan is Kaggle 2×T4 with Q4_K_M (`deploy/kaggle_evon.ipynb`). |
| Oct 11 | Prisma `connected` event always reports 16 kHz regardless of `x-sample-rate`; Kavach now always streams 16 kHz and simulates phone bandwidth locally. |
| Oct 11 | First eval (keywords only, 6 synthetic Hindi calls, phone line clean to 0 dB SNR): scams warned 3/3, false alarms 0/3 in every condition, Prisma CER ~4%, median warning ~17 s after first red flag. Noise is generated, not recorded. |
| Oct 11 | Exotel sales call booked for Oct 12, 4 PM (`EXOTEL_MEETING.md`, local only). |
| Oct 11 | Evon hosted on Kaggle (needed `GGML_CUDA_NO_VMM=ON` to build). Tuned: few-shot prompt, enforced JSON schema (4-bit model loops when copying Devanagari), fuzzy evidence guard, vote before HARD, greedy first pass. Found and fixed scorer bugs (UNCERTAIN muting keywords; unconfirmed SCAM race). |
| Oct 11 to 12 | 12 more hand-written calls (Evon-written ones unusable). Text eval: keywords 13/18, keywords + Evon 17/18 (miss: task job). **Audio eval, 18 calls x 2 phone conditions: 9/9 scams with HARD warnings, 0/9 false alarms, 0 Evon errors.** Credits used so far: about 45 of 5,000. |
| | **Next:** live Guardian test with a real phone on speaker; Telegram bot; warn faster (12 to 16 s after first red flag); voice clone with consent; review the 12 Hindi scripts; Exotel sales follow-up (Mon to Fri); write the video script. |

### Open questions
- [ ] Registered for the challenge yet? Credits email received?
- [ ] Solo or duo?
- [ ] College city: Tier 2/3? (Small Town, Big Build eligibility)
- [ ] Who plays "mom"/scammer, and whose voice is cloned (consent)?
- [ ] Evon hosting: rented GPU vs Kaggle vs local?
- [ ] FAQ answers + programme terms read?
