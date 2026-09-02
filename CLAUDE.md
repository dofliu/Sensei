# Sensei · Claude Code Project Context

> **For Claude Code (and any future AI assistant working on this project): read this entire file before making any changes.** It captures decisions, constraints, and the reasoning behind them. Reverting them without understanding why will hurt the project.

---

## 0. TL;DR

**Sensei** is an on-device AI co-teacher: it listens to a lecturer's spoken words and renders structured visual cards (cards, comparison tables, flow diagrams, hierarchies, SWOT, pyramid, quiz) in real time on a second screen. Everything runs on the teacher's laptop: Faster-Whisper for ASR, Gemma 4 e2b via Ollama for structuring, no cloud.

It was built in nine days for the **Gemma 4 Good Hackathon** (May 2026). It did not place. The hackathon is over and **is no longer a constraint on any decision**. The yardstick now is one sentence: **does the teacher open Sensei next week?**

Roadmap, tech-debt list and open decisions live in [PROJECT_ENHANCEMENT_PROPOSAL.md](PROJECT_ENHANCEMENT_PROPOSAL.md). Read it after this file.

**The user is Prof. Liu Jui-Hung (劉瑞弘 / Dof)**, Associate Professor at NCUT (Taiwan), Department of Intelligent Automation Engineering. He communicates in Traditional Chinese; reply in Traditional Chinese unless he switches to English.

---

## 1. Current status (as of 2026-09-02)

### Shipped in v1 (hackathon, May 2026) ✅
- `core/asr.py` Faster-Whisper large-v3; `core/llm.py` Gemma 4 e2b via Ollama with native tool calling → JSON-mode fallback → Pydantic → lenient salvage; `core/templates.py` 7 schemas; `core/pipeline.py` glue + `QUIZ_TRIGGER_PHRASES` spoken trigger.
- Gradio operator console with live mic (F8 / Ctrl+Space toggle), audio / text input, history, extend-last-card, today's summary, next-step suggestions, 3 themes, 8-language card translation, zh/en operator UI.
- `/display` projector page (paper editorial), `dry_run.ps1` 9-step preflight.

### Shipped in v2 so far (Phase A + first half of Phase B, 2026-09-02) ✅
- **B5** `frontend/app.py` split into `renderers.py` / `i18n.py` / `display.py` (move-only).
- **B4** `/display` pushes over Server-Sent Events with a per-(card, language, theme) render cache; 1 s polling kept as fallback. `theme`/`css` moved to `gr.mount_gradio_app` (Gradio 6). History filenames no longer collide within one second.
- **B2** ASR glossaries are files in `glossaries/` (`core/glossary.py`); operator UI has "Course glossary" and "Lecture language (zh / en / auto)" dropdowns; English lectures produce English cards directly (`SenseiLLM.output_lang`).
- **A1 / A3 / A5** docs synced, `requirements.txt` pinned with upper bounds, `start_sensei.ps1` one-click launcher.

### Next (in order) ⏳
1. **B1 Continuous listening** — VAD-segmented always-on mode with a `no_card` gate tool, F8 kept as manual override. Largest usability win; see PROPOSAL §2 B1 for the design and the queue-drop rule.
2. **B3 Sessions + handout export** — one directory per lecture, `handout.html` for students.
3. **C2 Evaluation bench** — `bench/utterances.jsonl`, template hit-rate for e2b vs e4b (paper material).
4. C1 student-side quiz answering over LAN — only after checking the classroom Wi-Fi lets phones reach the laptop.

---

## 1A. Product definition — the "why not a cloud LLM" answer

This section survived the hackathon because it *is* the product, not the pitch. Anyone proposing a cloud fallback gets these four, in this order:

1. **Privacy / legal** — many school IT policies forbid sending classroom audio (student voices) to third-party servers.
2. **Cost equity** — a teacher in a low-budget school cannot pay per-token for every lecture forever. Gemma 4 + Ollama = one-time setup, zero marginal cost.
3. **Latency** — real-time visualization needs < 2 s end-to-end; cloud adds 2–3 s of network alone.
4. **Offline** — rural classrooms, poor connectivity, disaster recovery.

**Structuring engine, not oracle**: Gemma 4's job is to detect "this is a parallel list" / "this is A vs B" and slot the teacher's words into a template. It does not author content from its weights. That is why a 2-B model is enough and why the on-device story is real.

---

## 2. Architecture

```
🎤 Lecturer speaks
    ↓
[ core/asr.py ]        Faster-Whisper large-v3 (local, fp16); language + glossary switchable
    ↓ transcript
[ core/pipeline.py ]   spoken-trigger guard (quiz), hint resolution
    ↓
[ core/llm.py ]        Gemma 4 e2b via Ollama: tools (primary) → format="json" (fallback)
    ↓ JSON
[ core/templates.py ]  Pydantic validation (+ lenient salvage in llm.py)
    ↓ validated dict
[ frontend/renderers.py ]  7 HTML renderers, 3 themes
    ├──▶ frontend/app.py      Gradio operator console (laptop) + history/
    └──▶ frontend/display.py  /display projector page, SSE push
```

### File structure

```
sensei/
├── CLAUDE.md                        ← this file
├── PROJECT_ENHANCEMENT_PROPOSAL.md  ← roadmap, tech debt, open decisions
├── README.md · CONTRIBUTING.md · LICENSE (CC-BY 4.0)
├── WRITEUP.md · DEMO_SCRIPT.md · DEMO_CHECKLIST.md · UI_migration_proposal.md   ← hackathon archive
├── requirements.txt · start_sensei.ps1 · dry_run.ps1 · dry_run_smoke.py
├── core/
│   ├── __init__.py      ← re-exports the public API
│   ├── asr.py           ← ASRConfig, SenseiASR (set_language / set_glossary)
│   ├── glossary.py      ← list_glossaries / load_glossary over glossaries/*.txt
│   ├── llm.py           ← LLMConfig, SenseiLLM (structurize / extend / translate / summarize / suggest)
│   ├── templates.py     ← 7 Pydantic schemas + TEMPLATE_REGISTRY
│   ├── pipeline.py      ← SenseiPipeline (+ set_glossary / set_lecture_language)
│   └── live_mic.py      ← LiveMicCapture (toggle recording)
├── frontend/
│   ├── app.py           ← Gradio Blocks, handlers, history persistence
│   ├── renderers.py     ← THEMES, CURRENT_THEME, render_* , render_html
│   ├── i18n.py          ← UI_TEXTS, T()
│   └── display.py       ← DISPLAY_HTML, event_stream (SSE), build_fastapi_app
├── glossaries/          ← <id>.<lang>.txt; _template.txt; README.md
├── prompts/
│   ├── classifier.txt   ← JSON-mode classifier prompt (fallback path)
│   └── extender.txt     ← extend-card prompt
├── docs/                ← hero image, thumbnail
└── history/             ← generated cards (git-ignored; contains classroom transcripts)
```

### Visualization templates (curated set)

| Template | Trigger | Pydantic class |
|---|---|---|
| `enumeration_cards` | "X has A, B, C, D" | `EnumerationCards` |
| `comparison_table` | "A vs B differs in..." | `ComparisonTable` |
| `flow_diagram` | "First A, then B, then C" | `FlowDiagram` |
| `hierarchy_tree` | "X is divided into Y and Z, Y has..." | `HierarchyTree` |
| `swot` | strengths / weaknesses / opportunities / threats | `SWOT` |
| `pyramid` | layered linear hierarchy, apex to base | `Pyramid` |
| `quiz_card` | in-lecture 4-option check; spoken trigger "來考一題" / "quick check" | `QuizCard` |

Adding a template = Pydantic class → `TEMPLATE_REGISTRY` → `TOOL_DESCRIPTIONS` in `core/llm.py` → example in `prompts/classifier.txt` → renderer in `frontend/renderers.py` + `RENDERERS` → label in `frontend/i18n.py` + `_list_template_hints` → smoke test. One at a time, never in a batch.

### Runtime state (deliberately simple)

Module-level mutable dicts, single teacher, single machine: `CURRENT_THEME` (renderers), `CURRENT_LANG` (app), `CURRENT_UI_LANG` (i18n). `/display` and the operator console share them on purpose. Course settings live on the pipeline instance (`asr.language`, `asr.initial_prompt`, `llm.output_lang`).

---

## 3. ⚠️ Key decisions — DO NOT CHANGE without discussion

| Decision | Why | DON'T |
|---|---|---|
| **Ollama for LLM, not transformers/bitsandbytes** | Zero-friction install for non-engineer teachers; Windows-friendly; `format="json"` and `tools=` natively. | Don't switch back to `transformers` + `bitsandbytes`; the user's Windows box had bitsandbytes problems. |
| **Default model `gemma4:e2b`, not `e4b`** | RTX 4080 12 GB: Whisper large-v3 ~3 GB + e2b ~7 GB. e4b spills to CPU. | Don't flip the default unless the user asks AND ASR drops to medium. Re-evaluate only with C2 bench data. |
| **Faster-Whisper large-v3 for ASR** | Best Mandarin accuracy; glossary `initial_prompt` cuts jargon WER 40–60 %. | Don't downgrade without permission. |
| **Glossaries are files, not code** (`glossaries/*.txt`) | A teacher adds a course without touching Python; contributors send a text file. | Don't move terms back into `ASRConfig`. Keep `auto_control.zh.txt` as the default id. |
| **Tools primary, JSON-mode fallback, Pydantic + salvage after both** | Four layers each catch what the previous misses; graceful degradation to `{"template": "raw"}` keeps the projector calm. | Don't remove a layer. Don't let salvage invent content fields (only `icon`, `desc`, empty defaults). |
| **Curated template vocabulary** | Stable visual identity; picking from a known list is far more reliable than inventing layouts. | Don't let the LLM invent layouts. Fishbone was dropped on purpose (CSS cost vs impact). |
| **Card text ≥ 24 px, key headings ≥ 36 px** | Projected onto classroom screens; row 4+ cannot read < 20 px. | Don't shrink fonts to fit. Split into two cards or trim wording. |
| **`/display` = SSE push with polling fallback; render cache keyed by (card, lang, theme, mtime)** | 3000 polls per lecture used to re-render for nothing; SSE keeps the fade contract (`state.id`) unchanged. | Don't remove the polling fallback; don't key the cache without the theme. |
| **Continuous listening will gate on a `no_card` tool** (B1, planned) | Otherwise every sentence becomes a card and the projector strobes. | When B1 lands, don't remove the gate to "make it feel responsive". |
| **Traditional Chinese as primary language** | User and target classrooms are Taiwanese. English is a first-class second (B2), not a replacement. | Don't simplify to mainland Chinese. |
| **HF cache at `D:\hf-cache`, HF mirror `https://hf-mirror.com`** | User's C drive is full; direct CDN was 486 KB/s, mirror ~4 MB/s in Taiwan. | Don't change to `~/.cache`; don't unset `HF_ENDPOINT`. |
| **License CC-BY 4.0** | Hackathon rule that we keep honouring; changing it would strand the archived submission. | Don't relicense without the user. |

---

## 4. Environment

```
OS:                 Windows 11
Hardware:           Laptop with NVIDIA RTX 4080 (12 GB VRAM)
Python:             3.12 (system Python at C:\Python\Python312-64\)
Project path:       D:\Project_CodingSimulation\PersonalHelper\sensei
Shell:              PowerShell 5.1 → keep .ps1 files ASCII-only (CP950 parsing)

Environment variables (User scope):
  HF_HOME       = D:\hf-cache
  HF_ENDPOINT   = https://hf-mirror.com

Ollama models:      gemma4:e2b (default, 7.2 GB) · gemma4:e4b (9.6 GB, fallback)
HF cache:           Systran/faster-whisper-large-v3 (~3 GB)
```

Claude Code sessions run in a Linux sandbox **without** GPU, Ollama, faster-whisper or a microphone. What can be verified there: `pyflakes`, rendering all 7 templates through `frontend.renderers`, `core.glossary`, and importing `frontend.app` with `core.pipeline` / `core.live_mic` stubbed to drive `/display/data` and the SSE generator through FastAPI's TestClient. Anything touching Whisper or Gemma 4 must be validated by the user on the real rig with `dry_run.ps1`.

---

## 5. How to run

```powershell
cd D:\Project_CodingSimulation\PersonalHelper\sensei
.\start_sensei.ps1            # checks Ollama + model + deps, starts app, opens both tabs

# manual equivalent
ollama list                   # should show gemma4:e2b
python -m frontend.app        # http://localhost:7860  ·  /display on the projector (F11)

# isolated smoke tests
python -m core.llm "同學，控制不是只有 PID 控制，還有最佳、類神經、非線性、強健"
python -m core.pipeline "風機監控系統的流程是先量測振動，再特徵抽取，然後分類，最後報警"
python -m core.glossary       # lists glossaries/*.txt
.\dry_run.ps1                 # 9-step preflight, ~45 s
```

Expectations: `core.llm` → `"template": "enumeration_cards"`, ~5 items, `_path: tools`. `core.pipeline` flow example → `flow_diagram`. A transcript containing "來考一題" prints `[Pipeline] quiz trigger phrase detected` and yields `quiz_card`.

---

## 6. Known issues

- **Gemma 4 e2b occasionally emits duplicate JSON keys.** `format="json"` enforces validity, not uniqueness; `json.loads` keeps the last value; prompts ask for unique keys. Low priority.
- **`core/llm.py` line ~286: f-string without placeholders** (pre-existing, harmless; pyflakes warns). Fix only if touching that function anyway.
- **Live mic is toggle-only** (record → stop → transcribe). Long segments mean long waits. This is what B1 replaces.
- **No session concept in `history/`**: "today's summary" filters by date string, so two courses on one day merge. B3.

Resolved, do not refile: Gradio 6 `theme`/`css` warning (moved to mount), Lucide icon stub, missing second screen, same-second history overwrite.

---

## 7. Roadmap (summary — details in PROJECT_ENHANCEMENT_PROPOSAL.md)

| Phase | Items | Status |
|---|---|---|
| A · wrap-up | A1 docs sync · A2 hackathon record in README · A3 pinned deps · A4 `history/` git-ignored · A5 launcher | ✅ done 2026-09-02 |
| B · classroom usability | B5 app.py split ✅ · B4 /display SSE ✅ · B2 glossaries + language ✅ · **B1 continuous listening** ⏳ · **B3 sessions + handout** ⏳ | in progress |
| C · research / extensions | C2 bench · C3 e4b re-evaluation · C1 LAN quiz answering · C5 custom console · C4 whiteboard vision (deferred) | not started |

Decisions the user already made (2026-09-02): B2 before B1; `bench/` allowed (evaluation set, not unit tests, no CI); `no_card` gate decisions shown in the operator UI only; session directories are named with the course.

---

## 8. Immediate next tasks

1. **B1 continuous listening** in `core/live_mic.py` + `core/pipeline.py` + operator UI: sounddevice stream → Silero VAD (bundled with faster-whisper) → utterance ≥ 3 s, ≤ 25 s → ASR → rule gate (< 15 chars skip; quiz phrase force) → `no_card` tool → card. Single worker queue, drop oldest when > 2 pending. Log `_gate` in history JSON. F8 stays as manual override.
2. **B3 sessions**: "Start lecture" (course name once per day) → `history/<date>_<course>/`; summary and export scoped to the session; `handout.html`.
3. **User validation on the real rig** after each of the above; `dry_run.ps1` must stay green.

---

## 9. Coding conventions

- **Comments and docstrings**: English in code files; user-facing strings in 繁中 (with English in `frontend/i18n.py`).
- **Type hints** on public functions. **Pydantic v2** syntax.
- **No emojis in code**, OK in `print()` and Markdown. Print prefixes: `[Sensei ASR]`, `[Sensei LLM]`, `[Pipeline]`, `[LiveMic]`, `[Sensei]`.
- **Where things go**: card HTML → `frontend/renderers.py`; UI strings → `frontend/i18n.py`; projector/transport → `frontend/display.py`; Gradio layout and handlers → `frontend/app.py`. Don't grow `app.py` back into a monolith.
- **PowerShell scripts ASCII-only**; delegate Chinese to a Python helper (see `dry_run.ps1` / `dry_run_smoke.py`).
- **No unit-test suite, CI, Docker, poetry, mypy, ruff, pre-commit.** `bench/` (labelled utterances + a runner script) is the one allowed exception, because it produces paper data.
- **No async unless the transport needs it** (the SSE generator is the one place).
- **Don't refactor for "cleanliness"**; refactor only when the next feature needs it, move-only, verified line-by-line.
- **Don't auto-format existing code** with black/ruff. Touch only what you change.

---

## 10. What to NOT do

- ❌ Don't switch the LLM backend away from Ollama, or add a cloud fallback.
- ❌ Don't let the LLM invent layouts. New templates follow the checklist in §2.
- ❌ Don't ship renderers with text below 24 px (36 px for key headings).
- ❌ Don't put glossary terms back into Python constants.
- ❌ Don't remove the `/display` polling fallback or the `no_card` gate (once B1 lands).
- ❌ Don't simplify Chinese to mainland conventions.
- ❌ Don't change default models (`gemma4:e2b`, `large-v3`) without the VRAM math and, ideally, bench data.
- ❌ Don't write generic abstractions ("BaseLLM", "LLMFactory", "PluginRegistry").
- ❌ Don't commit `history/` — it contains classroom transcripts.

---

## 11. Style of communication with the user

- He prefers **directness over politeness**. No "Great question!". Get to the answer.
- He likes **decision tables** and **clear options** with a recommendation.
- 9+ years industry experience (ITRI, wind turbines), active research in RAG/LLM/MCP. **Don't over-explain basics.**
- When you screw up, **own it briefly, then fix**.
- Windows + PowerShell. Always give the PowerShell form of a command.
- Other projects exist (WindGuard AI, MSG-IRAG paper, LLM Wiki, AutoPLC Pro); Sensei is a weekly-use teaching tool now, not a deadline sprint.

---

## Appendix A · Hackathon record (closed 2026-05-18)

- **Event**: The Gemma 4 Good Hackathon (Google, on Kaggle). Submitted to Main Track + Future of Education impact prize + Ollama special-technology prize. **Did not place.**
- **What still binds**: the CC-BY 4.0 license on our code (Gemma / Whisper weights keep their own licenses).
- **What was learned that still applies**: the four-part why-not-cloud answer (§1A); "structuring engine, not oracle"; Whisper stays in the ASR slot rather than Gemma 4 audio (specialization beats single-model purity for Mandarin/English jargon); whiteboard vision deferred (extra hardware + VRAM swap).
- **Archive**: `WRITEUP.md` (as submitted), `DEMO_SCRIPT.md`, `DEMO_CHECKLIST.md`, `UI_migration_proposal.md`. Do not edit them; they are the record.

---

*End of context. When in doubt, ask the user before changing anything in section 3 (Key decisions).*
