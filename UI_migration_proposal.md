# Sensei · UI Migration Proposal

> **Audience**: Claude Code (technical evaluator) + Prof. Liu
> **Date**: 2026-05-10
> **Deadline pressure**: Hackathon submission 2026-05-18 23:59 UTC (8 days)
> **Source of design**: `index.html` in the design project — Console-mode teacher console + paper classroom projector. Two-screen split, English UI, judge-friendly pipeline indicator.

---

## 0. TL;DR

The current Gradio UI cannot reach the visual fidelity the demo video needs. **The classroom projector view (`/display`) is what evaluators actually watch**, and it must look like paper editorial — not a Gradio panel.

**Recommendation: a hybrid, two-pass migration.**

1. **Pass 1 (Day 1, ~4 hrs)** — Replace `/display` with a hand-written HTML/CSS template. Keep Gradio for the teacher operator UI. Demo-impact: 80% of the win, with minimal risk.
2. **Pass 2 (Day 2–3, ~8 hrs, optional)** — Replace Gradio operator with a vanilla JS "Console" page served by FastAPI. Demo-impact: better hero shots in the video, but adds risk.

If time allows only one, **do Pass 1**. Pass 2 is a polish pass.

---

## 1. Current state — what we have today

From `frontend/app.py`:

- **Single Gradio app** at `:7860`. `THEMES` dict defines `dark` / `light` variants.
- Renderers are server-side Python f-strings producing HTML.
- A `/display` route is mounted via FastAPI for the second-monitor projection (referenced in CLAUDE.md as the "second monitor view").
- Card schemas in `core/templates.py`: `enumeration_cards`, `comparison_table`, `flow_diagram`, `hierarchy_tree`, `swot`, `pyramid`.
- `core/pipeline.py` orchestrates ASR (`asr.py` — Whisper L-V3) → LLM (`llm.py` — Gemma 3n via Ollama) → JSON → renderer.

**What works against us for the demo video:**

- Gradio chrome (footer, "Built with Gradio" attribution, default fonts, default focus rings) reads as "AI tech demo" not "tool a teacher actually uses."
- The dark/light themes are generic SaaS gradients. The chosen design direction is **warm paper / classroom**, which Gradio cannot natively express.
- Gradio components are interactive widgets; the projector view should be **read-only, full-bleed, no controls, no chrome**. Gradio fights this.
- Typography: Gradio defaults to system fonts; the design uses Instrument Serif + Geist + JetBrains Mono.

---

## 2. Design we are migrating toward

(See `index.html` in the design project — the "Console mode" main artboards.)

- **Two surfaces, intentionally different**:
  - **Teacher · Console** (laptop): ink-dark, dense, every signal visible — record button, waveform, transcript stream, pipeline indicator (Mic → Whisper → Gemma → Card), latency/VRAM metrics, gallery thumbnails, mirrored thumbnail of the projector.
  - **Classroom · Projector** (`/display`): paper warm background, controls-free, full-bleed card, subtle paper grain, "● ON-DEVICE · NOTHING LEAVES THE ROOM" footer.
- **Type pairing**: Instrument Serif (display headings) · Geist (body) · JetBrains Mono (system labels, "META").
- **Palette**:
  - Paper: `#f6f1e6` (paper), `#efe7d3` (paperDeep), `#29261b` (ink), `#7a6a52` (mute), `#d8cdb3` (line)
  - Ink: `#0f0d0a` paper, `#f4eddb` ink, `#3a322a` line
  - Accents (oklch, low-chroma): warm orange `#D97757`, deep blue `#1F3A6E`, sage `#4A7C59`
- **Pipeline indicator** is a first-class visual element (judges asked for it in the questionnaire).
- **English copy** throughout (judge-facing).

---

## 3. The three options

### Option A — Replace `/display` only (RECOMMENDED for Pass 1)

**What changes**

- Add `frontend/static/display.html`, `frontend/static/tokens.css`, `frontend/static/cards.css`.
- FastAPI's `/display` route returns `display.html` with the latest card JSON injected (via SSE or `<script>JSON.parse</script>` snapshot).
- Card renderers ported from Python f-strings to **client-side templates** (vanilla JS, no React), so card-type swaps fade in cleanly.
- Existing Gradio app keeps running as the operator surface. No backend changes beyond the `/display` route.

**Why this first**

- The projector view is what the **3-minute demo video** lingers on. CLAUDE.md says "the demo video is the most important deliverable."
- The teacher's laptop is barely on-screen during the demo — fidelity there matters less.
- Zero risk to the working pipeline. The Gradio operator surface remains untouched and shippable.

**Effort**: ~4 hrs (one focused session)

**Files to add**

```
frontend/static/display.html       ~150 lines
frontend/static/tokens.css         ~40  lines  (CSS custom props)
frontend/static/cards.css          ~250 lines  (per-template styling)
frontend/static/cards.js           ~200 lines  (renderers + fade-swap)
```

**Backend changes**

- One FastAPI route returns `display.html` and mounts the static dir.
- Reuse the existing card-update mechanism (whatever currently feeds `/display`). If it's polling-based, keep it; if SSE, keep it. **Don't rewrite the transport.**

---

### Option B — Replace operator (Gradio) too

**Path B1 — `gr.HTML` + Gradio control widgets, CSS-disguised**

- Stuff the Console layout into `gr.HTML`, leave a few real Gradio inputs (record button, template select, file upload) hidden behind the design.
- **Verdict: don't.** It's a maintenance pit. Gradio's component DOM fights every CSS reset. Focus rings, ARIA labels, and event wiring all leak through.

**Path B2 — Drop Gradio, add a `/console` route**

- FastAPI serves `console.html` (vanilla JS or htmx). WebSocket pushes pipeline state, transcript chunks, and card JSON.
- Microphone capture moves to **browser** (`MediaRecorder` API) — chunks POSTed to `/asr`. Removes the desktop-recording dependency from `core/live_mic.py` for the web flow (keep `live_mic.py` for the CLI smoke path).

**Why this is risky right now**

- WebSocket plumbing + browser mic permissions = a non-trivial debug session 4 days before submission.
- Hotkey global F8 (CLAUDE.md mentions it) doesn't work the same in a browser tab — needs focus, can't capture global shortcuts. May need to fall back to a click-to-record button only.
- If the ASR worker is stateful (rolling 30-sec buffer mentioned in CLAUDE.md), wiring browser-chunked audio into it is more delicate than it sounds.

**Effort**: ~8–12 hrs, with real failure modes (WebSocket reconnect, audio chunk alignment, cross-browser mic).

**When to do it**: only after Pass 1 ships and the demo recording is in the can. Treat it as a Day 6+ polish.

---

### Option C — Tokens-only handoff

- I produce `tokens.css` + 4 template HTML samples; Prof. Liu pastes them into the Python f-string renderers.
- **Verdict: skip.** Saves my time, costs his. The hackathon clock is on him, not on me.

---

## 4. Recommended plan

| Day | Task | Owner | Deliverable |
|---|---|---|---|
| Today (Day 1) | Pass 1 — `/display` rewrite | Prof. Liu + Claude Code | `frontend/static/display.html` + tokens + renderers; demo-quality projector view |
| Day 2 | Real classroom audio test against new `/display` | Prof. Liu | Confirm card swaps look smooth on actual projector |
| Day 3–5 | Buffer for ASR/LLM tuning | Prof. Liu | (no UI work) |
| Day 6 | Decide: ship operator-as-Gradio, or attempt Pass 2 | Prof. Liu | Go/no-go |
| Day 6–7 | (If go) Pass 2 — `/console` route | Prof. Liu + Claude Code | Replaces Gradio operator |
| Day 7 | Demo video shoot | Prof. Liu | The deliverable |
| Day 8 | Final polish + writeup | Prof. Liu | Submission |

**Hard rule**: if anything in Pass 2 is not working by end of Day 6, **revert to Gradio operator** and ship. The video is what matters.

---

## 5. Concrete Pass 1 work breakdown

### 5.1 New files

```
frontend/static/
  tokens.css            CSS variables: --paper, --ink, --mute, --line,
                        --accent-warm, --accent-blue, --accent-sage,
                        --serif, --sans, --mono, --space-1..6
  display.html          Full-bleed paper page; "SENSEI · /display" header,
                        lecture/clock readout, card slot, on-device footer
  cards.css             Per-template visual styling (paper card chrome,
                        meta strip, accent rules, table grid lines)
  cards.js              renderEnumeration(), renderCompare(),
                        renderFlow(), renderPyramid(), renderSwot(),
                        renderHierarchy() + a fade-swap host
  fonts.css             Google Fonts @import (Instrument Serif, Geist,
                        JetBrains Mono) — single line, easy to swap for
                        local files later
```

### 5.2 `frontend/app.py` changes

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.get("/display")
def display():
    return FileResponse("frontend/static/display.html")

# Keep whatever endpoint already pushes card JSON to /display.
# If it's a polling endpoint returning the latest card, no change.
# If it's SSE, the new cards.js subscribes to the same channel.
```

### 5.3 Card data contract (must not change)

`cards.js` consumes the **same JSON** that `core/templates.py` validates today. Don't refactor the schema. Each renderer is a pure function: `(json) → HTMLElement`. The fade-swap host swaps the active card with a 200 ms ease.

### 5.4 What to NOT do in Pass 1

- ❌ Don't touch `core/asr.py`, `core/llm.py`, `core/pipeline.py`, `core/templates.py`.
- ❌ Don't add WebSockets if the current transport works.
- ❌ Don't add a build step (no React, no Vite, no TypeScript). One `<script>` tag, period.
- ❌ Don't port the operator yet.

---

## 6. Pass 2 work breakdown (only if Pass 1 ships clean)

### 6.1 New files

```
frontend/static/
  console.html          Teacher operator UI — ink palette, dense layout
  console.css           Console-specific styling
  console.js            WebSocket client, pipeline state machine,
                        transcript streaming, gallery, mirror thumbnail
```

### 6.2 Backend additions

```python
@app.get("/console")
def console():
    return FileResponse("frontend/static/console.html")

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    # Push: {type: "asr_chunk", text: "..."}
    #       {type: "pipeline", state: "asr|llm|done"}
    #       {type: "card", data: {...}}
    # Recv: {type: "record_start"} / {type: "record_stop"}
    #       {type: "template_hint", value: "flow_diagram"}
```

### 6.3 Microphone

- Browser `MediaRecorder({ mimeType: 'audio/webm;codecs=opus' })`, 1 second chunks.
- Each chunk POSTed to `/asr_chunk`; server appends to the rolling buffer.
- If `core/live_mic.py` already implements a clean buffer interface, replace its capture source with the HTTP-chunk source.

### 6.4 Hotkey caveat

Global F8 (mentioned in CLAUDE.md) is a desktop-app feature. In a browser tab the hotkey only works while the tab has focus. **Document this.** If the demo flow needs a global hotkey, keep `live_mic.py` running alongside as a sidecar, posting the same WebSocket events.

---

## 7. Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Pass 1 cards.js renderer drifts from `core/templates.py` schema | Medium | Lock schema; add a `tests/test_renderers.html` page that loads each sample JSON from `history/` and renders all six templates |
| Fonts don't load on classroom Wi-Fi at demo time | Low | After Pass 1, download fonts to `frontend/static/fonts/` and switch `fonts.css` to local `@font-face` |
| Gradio still drags down operator-side polish for the video | High if Pass 2 skipped | Frame the demo video with the projector full-screen; cut to operator only briefly |
| Pass 2 WebSocket + mic chunking eats Day 7 | Medium | Hard cutoff at end of Day 6; revert to Gradio operator, video still ships |
| Card swap animation jank during demo | Low | 200 ms fade with `prefers-reduced-motion` opt-out; preload next card hidden |

---

## 8. Open questions for Prof. Liu

1. Does `/display` already exist in `app.py`, and what's the current transport (polling? SSE? FastAPI long-poll?)? Pass 1 should reuse it.
2. Is the demo video shot with **two real screens** (laptop + projector) on camera, or is `/display` framed full-screen? This determines whether Pass 2 is worth the risk.
3. Can the demo classroom run **on-device only** (no Wi-Fi) the day of recording? If so, Pass 1 must inline fonts.
4. Is `core/live_mic.py` finished, and does it expose a clean "give me the last 30 seconds of audio" interface? (Decides Pass 2 mic strategy.)

---

## 9. What Claude Code is being asked to evaluate

Please assess:

1. **Is the Pass 1 / Pass 2 split correct given the actual `app.py` shape?** I have only skimmed the file — there may be Gradio-FastAPI integration details that change the cost estimate.
2. **Is the `/display` transport reusable as-is**, or does it need a small refactor before the new HTML page can subscribe to it?
3. **Is dropping Gradio entirely (Pass 2) realistic in 8–12 hours**, given the actual ASR worker shape and the live-mic loop? You see the code; I'm guessing.
4. **Are there hackathon judging criteria** (e.g. "must run as a single command") that the proposed split violates?
5. **Anything I missed.**

If Pass 1 looks good, the next concrete deliverable is the four files in `frontend/static/`. The design project (`index.html` in the Onlook project) has the visual reference and the working renderer code in `cards.jsx` — that's the source to port from. Render contract is preserved; only the visual layer changes.
