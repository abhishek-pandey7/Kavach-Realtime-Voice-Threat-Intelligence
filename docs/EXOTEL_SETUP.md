# Merge-in mode with Exotel

Merge-in mode lets Kavach join a real phone call. The user taps **Bulao Kavach**, Exotel rings their phone, they answer and **merge** it into the suspicious call. Exotel then streams the merged call audio to Kavach, and Kavach's warnings play back into the call for everyone to hear.

Status: the code is written against Exotel's documented AgentStream protocol but not yet tested on a live account.

**Blocked on KYC (Oct 12, 2026).** Exotel Sales confirmed the Voicebot applet is enabled by default, but **KYC is required to add a number (ExoPhone) and to test outbound calls**, and both are needed here. Exotel's KYC asks for business documents (GST, MSME or shop licence), which an individual student doesn't have. Asked whether trial accounts get a test number or an individual (PAN + Aadhaar) KYC route; waiting for the reply. If neither is possible, merge-in mode stays a "next step" and Guardian mode is the demo. Decision date: Oct 20.

## 1. Credentials

In the Exotel dashboard, **Settings → API Settings**, copy the values into `.env` (never into chat or commits):

```
EXOTEL_SID=elyratechnologies1
EXOTEL_API_KEY=...
EXOTEL_API_TOKEN=...
EXOTEL_SUBDOMAIN=api.in.exotel.com
EXOTEL_CALLER_ID=<an ExoPhone on the account, e.g. 0XXXXXXXXXX>
PUBLIC_WSS_BASE=wss://<your tunnel host>
```

## 2. Start Kavach and a public tunnel

```bash
.venv/Scripts/python -m kavach.web.app          # dashboard on http://localhost:8765
cloudflared tunnel --url http://localhost:8765  # prints https://xxxx.trycloudflare.com
```

Set `PUBLIC_WSS_BASE=wss://xxxx.trycloudflare.com` (same host, `wss://`) and restart the app. On Windows, install cloudflared with `winget install --id Cloudflare.cloudflared`. ngrok works too.

## 3. Echo test (do this first)

Check that audio flows both ways before involving Kavach:

```bash
.venv/Scripts/python scripts/exotel_call.py --to +91XXXXXXXXXX --echo
```

Answer the call and speak. You should hear yourself back about a second later. If you don't:
- Is AgentStream (bidirectional Voicebot) enabled on the account?
- Is the number verified (trial accounts only call verified numbers)?
- Does the tunnel URL in `PUBLIC_WSS_BASE` match the running tunnel?
- The app log shows `Exotel stream ... started` when Exotel connects.

## 4. Alternative: inbound flow (App Bazaar)

Instead of Kavach calling the user, the user can call (or merge in) an ExoPhone that runs a Voicebot flow. This also needs a KYC'd number.

1. **App Bazaar → Create**, add a **Voicebot** applet, URL `wss://<tunnel host>/exotel/ws?lang=hi-IN` (at most 3 query parameters, 256 characters in total).
2. Exotel support asked for **Record** to be enabled on the applet. That stores a recording of the call on Exotel's side, which conflicts with Kavach's "no storage" design: ask whether it can be off, and if not, use it only for consented test calls and say so in the README.
3. Add a **Passthru** applet right after the Voicebot (Exotel's recommendation: it logs stream metadata and detects disconnects), then **Hangup**.
4. Attach the flow to the ExoPhone and save.

Kavach keeps the WebSocket open for the whole call; closing it moves Exotel to the next applet.

## 5. Kavach on a real call

1. Open the dashboard. When the Exotel variables are set, a **Bulao Kavach** box appears.
2. From another phone, a friend calls you and reads a scam script (staged, with consent).
3. Enter your verified number and press **Bulao Kavach** (or run `scripts/exotel_call.py --to +91...`).
4. Answer Exotel's call; your phone puts the friend on hold. Tap **Merge**.
5. The dashboard shows the live transcript and risk. Kavach's warning plays into the merged call.

## Notes

- Kavach requests 16 kHz audio (`?sample-rate=16000` on the stream URL) so it goes to Prisma unchanged. If Exotel ignores the parameter, the adapter resamples whatever rate the `start` event reports.
- Outbound audio is sent in 200 ms chunks (multiples of 320 bytes, at least 3,200 bytes) followed by a `mark`; Kavach waits for Exotel's mark before treating the warning as played.
- Pipecat's Exotel guide warns that query parameters can be stripped in some flows; if `lang` is lost, the call defaults to Hindi.
- Max stream length is 60 minutes.
- Exotel's guide: the bot must answer within 10 seconds or the session fails, Exotel retries a failed handshake once, and `wss://` needs a valid certificate (the Cloudflare tunnel provides one).
- Default stream audio is 8 kHz, 16-bit PCM, mono, about 100 ms per `media` event.
