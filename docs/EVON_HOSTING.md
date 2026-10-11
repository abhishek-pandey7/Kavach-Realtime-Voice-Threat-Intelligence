# Hosting Evon v3.3

Evon is not on Gnani's API, so Kavach talks to it through any OpenAI-compatible server. Once a server is running, put its address in `.env`:

```
EVON_BASE_URL=https://<your-server>/v1
EVON_MODEL=model
EVON_API_KEY=<the key you set on the server>
```

Then check it:

```bash
.venv/Scripts/python scripts/evon_check.py
```

This prints a verdict and the latency for a scam call and two genuine calls.

## Model facts that matter for hosting

- 30B total parameters, about 3.5B active per token (hybrid Mamba2-Transformer MoE, architecture `nemotron_h`).
- Official weights: [gnani/gnani-evon-v3.3-30B-A3B](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B), BF16, about 60 GB. Needs vLLM 0.12+ or SGLang.
- Community GGUF: [luminenio/gnani-evon-v3.3-30B-A3B-GGUF](https://huggingface.co/luminenio/gnani-evon-v3.3-30B-A3B-GGUF). The model card says downloads need approval, but as of Oct 11, 2026 the repo is **not gated**: the Hub API reports `gated: false` and files download without logging in. Sizes: Q4_K_M 23.0 GB, IQ4_XS 17.1 GB, Q8_0 31.5 GB. Needs a recent llama.cpp with `nemotron_h_moe` support.
- Recommended sampling: temperature 0.6, top_p 0.95. Kavach turns thinking off for live verdicts (`chat_template_kwargs: {"enable_thinking": false}`).

## Option A: Kaggle, free (recommended to start)

**Fastest path:** import `deploy/kaggle_evon.ipynb` into Kaggle (**File → Import Notebook**), set **GPU T4 x2** and **Internet on**, then **Run All**. It builds llama.cpp, downloads Evon, starts the server, runs a Hindi test and prints the three `.env` lines. The manual steps below do the same thing.

Kaggle gives 2 × T4 GPUs (32 GB VRAM total) for about 30 GPU-hours a week. Q4_K_M (23 GB) fits entirely on the GPUs.

Before you start:
1. On Kaggle, verify your phone number (needed for internet access in notebooks).
2. Create a notebook (or use **Use this model → Kaggle** on the Hugging Face repo page). Settings: **Accelerator: GPU T4 x2**, **Internet: on**.
3. No Hugging Face token is needed while the repo stays ungated. If downloads start failing with 401/403, add a read token under **Add-ons → Secrets** as `HF_TOKEN` and run `os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")` before downloading.

Notebook cells:

```bash
# 1. Build llama.cpp with CUDA (about 10 to 15 minutes)
!git clone --depth 1 https://github.com/ggml-org/llama.cpp
!cd llama.cpp && cmake -B build -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release && cmake --build build -j --target llama-server
```

```bash
# 2. Download the model (23 GB, plus licence files)
!pip -q install -U huggingface_hub
!hf download luminenio/gnani-evon-v3.3-30B-A3B-GGUF gnani-evon-v3.3-30B-A3B-Q4_K_M.gguf LICENSE LICENSE-NVIDIA NOTICE --local-dir /tmp/models
!df -h /tmp && ls -lh /tmp/models
```

```bash
# 3. Start the server in the background (pick a long random API key)
!nohup ./llama.cpp/build/bin/llama-server \
    -m /tmp/models/gnani-evon-v3.3-30B-A3B-Q4_K_M.gguf \
    -ngl 99 -c 16384 --jinja \
    --host 0.0.0.0 --port 8080 --api-key CHANGE_ME_LONG_RANDOM \
    > server.log 2>&1 &
!sleep 60 && tail -5 server.log
```

```bash
# 4. Expose it with a free Cloudflare quick tunnel (no account needed)
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared && chmod +x cloudflared
!nohup ./cloudflared tunnel --url http://localhost:8080 > tunnel.log 2>&1 &
!sleep 10 && grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' tunnel.log
```

Put the printed URL plus `/v1` in `EVON_BASE_URL`, and the API key in `EVON_API_KEY`.

Notes:
- The tunnel URL changes every session. Kaggle sessions stop after 12 hours or when idle.
- The model goes to `/tmp/models` because Kaggle's `/kaggle/working` folder is capped at about 20 GB, smaller than the 23 GB file. `/tmp` is wiped when the session ends, so the download (a few minutes) repeats each session. Check the free space shown by `df -h /tmp` before downloading.
- If the build fails on `nemotron_h_moe`, the repo notes it was tested at llama.cpp commit `8b4b3558f1459c13e4aa38d5c94d306a00dc6acd`; check that commit out instead of the latest.

## Option B: rented GPU with vLLM (for demo filming)

For the lowest latency during filming, rent a single 80 GB GPU (A100 or H100) by the hour on a GPU cloud and run the official BF16 weights:

```bash
pip install -U "vllm>=0.12.0"
vllm serve gnani/gnani-evon-v3.3-30B-A3B \
  --served-model-name model \
  --max-model-len 16384 \
  --trust-remote-code \
  --reasoning-parser nano_v3 \
  --api-key CHANGE_ME_LONG_RANDOM \
  --host 0.0.0.0 --port 8000
```

Only run it while testing or filming, and shut it down afterwards.

## Option C: this laptop (not recommended)

The laptop has a 6 GB RTX 4050 and 16 GB RAM. The smallest usable file (IQ4_XS, 17 GB) does not fit in RAM plus VRAM with the OS running, so local Evon is not practical. Kavach keeps working without Evon: the keyword layer still runs, and the pipeline treats a missing Evon verdict as UNCERTAIN.

## What to measure once it runs

- Latency of `scripts/evon_check.py` for each case (target under 2 s with thinking off).
- Whether the two genuine calls come back SAFE or UNCERTAIN, not SCAM.
- Whether the warning text is natural Hindi.
Write the numbers into the status log in `PLAN.md`.
