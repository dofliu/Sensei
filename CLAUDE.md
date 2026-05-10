# Sensei · Claude Code Project Context

> **For Claude Code (and any future AI assistant working on this project): read this entire file before making any changes.** It captures decisions, constraints, and the reasoning behind them. Reverting them without understanding why will hurt the project.

---

## 0. TL;DR

**Sensei** is an on-device AI co-teacher: it listens to a lecturer's spoken words and renders structured visual cards (cards, comparison tables, flow diagrams, hierarchies) in real time on a second screen. **Submission for the Gemma 4 Good Hackathon, Education track, deadline 2026-05-18 23:59 UTC** (9 days from project start on 2026-05-09).

The **single most important deliverable is a 3-minute demo video** of a real classroom. Technical polish matters less than a clear, emotionally resonant demonstration that "this helps real teachers."

**The user is Prof. Liu Jui-Hung (劉瑞弘 / Dof)**, Associate Professor at NCUT (Taiwan), Department of Intelligent Automation Engineering. He communicates in Traditional Chinese; reply in Traditional Chinese unless he switches to English.

---

## 1. Current status (as of 2026-05-09 evening)

### Working ✅
- `core/asr.py` — Faster-Whisper large-v3 loads + transcribes
- `core/llm.py` — Gemma 4 e2b via Ollama, JSON-mode output, Pydantic validation
- `core/templates.py` — 4 schemas validated
- `core/pipeline.py` — end-to-end glue
- Smoke test passed: `python -m core.llm "..."` returns valid JSON for the canonical example ("控制不是只有 PID...")

### Just-fixed (verify still working) 🔧
- `frontend/app.py` — had Gradio 6.0 API issues (`theme` moved to `launch()`, `show_api` removed). Should be patched. Run `python -m frontend.app` and confirm Gradio launches at http://localhost:7860.

### Not yet started ⏳
- Live mic streaming (rolling 30-sec buffer, hotkey trigger) — Day 3 priority
- Theme switching (light / paper themes; current is dark only) — approved 2026-05-09
- ~~SWOT / pyramid templates~~ — shipped 2026-05-09; ~~fishbone~~ dropped 2026-05-09 (CSS cost too high for low impact)
- Native Gemma 4 function-calling refactor (currently using prompt + JSON mode) — Day 5
- Domain glossary expansion (currently only auto-control terms)
- Real classroom audio testing pass — Day 4
- Real classroom demo video — Day 7 (the deliverable)
- Technical write-up (`WRITEUP.md`) — start drafting Day 1A in parallel

---

## 1A. The Hackathon: rules, judging, and our positioning

> Critical context for any feature decision, and especially for writing the Day 8 technical writeup.

### The competition

- **Name**: The Gemma 4 Good Hackathon
- **Host**: Google LLC, hosted on Kaggle
- **URL**: https://www.kaggle.com/competitions/gemma-4-good-hackathon/
- **Total prize pool**: USD $200,000 across three independent pools (see below)
- **Final submission deadline**: 2026-05-18, 23:59 UTC
- **License (per rules §1.6 + §2.5.a)**: winning submissions and their source code must be released under **CC-BY 4.0**. (Unusual for code — CC-BY is normally a content license — but it's what Google chose.) Apache 2.0 is *not* compliant.
- **Submission cap (per rules §2.2.a)**: each Team may submit **exactly one (1) Submission**. No leaderboard iteration. The Day 10 click is final.

### Prize structure — Sensei targets THREE pools simultaneously

The rules explicitly state: *"Projects are eligible to win both a Main Track Prize and a Special Technology Prize."* That permits stacking. Impact-vs-Main stacking is not explicitly addressed; the writeup self-nominates Sensei for all three buckets and lets the judges decide.

| Prize pool | Prizes | Sensei's fit |
|---|---|---|
| **Main Track** ($100k) | 1st $50k / 2nd $25k / 3rd $15k / 4th $10k — best overall projects | Compete on the merits of the full submission |
| **Impact Track** ($50k) | 5 × $10k categories: Health & Sciences, Global Resilience, **Future of Education** ⭐, Digital Equity & Inclusivity, Safety & Trust | ⭐ **Future of Education** — direct fit. Official wording: *"Reimagine the learning journey by building multi-tool agents that adapt to the individual and empower the educator through seamless integration."* |
| **Special Technology Track** ($50k) | 5 × $10k: Cactus, LiteRT, llama.cpp, **Ollama** ⭐, Unsloth | ⭐ **Ollama** — Sensei's entire backend is Ollama; tailor-made. Official wording: *"For the best project that utilizes and showcases the capabilities of Gemma 4 running locally via Ollama."* |

Hackathon community analysis (from public commentary on the competition) flags **Education as one of the strongest sub-tracks if executed well** — judges are explicitly looking for tools that help underserved learners and teachers.

### Other notable rule constraints

- **No HF Spaces / demo URL required** in the rules text — confirmed safe to drop (decision recorded above).
- **Team size** capped at 5; Sensei is currently solo (potential to recruit Kiwi or Christian if useful, separate decision).
- **External data and tools** allowed if "reasonably accessible to all" and "minimal cost" — Gemma 4 + Faster-Whisper + Ollama all qualify.
- **Open-source dependencies** must use OSI-approved licenses (rules §3.6.c) — all our deps (gradio, fastapi, pydantic, faster-whisper) qualify.
- **Pretrained models with incompatible licenses** don't have to be relicensed under CC-BY 4.0 (rules §2.5.a) — Gemma weights stay under Google's license, our code goes CC-BY 4.0.

### What judges score on (three pillars)

| Pillar | What it means for Sensei |
|---|---|
| **1. Real-world impact** | The single biggest weight. We need a *clear, named beneficiary*: under-resourced classroom teachers worldwide who can't afford slide-design time or cloud AI subscriptions. The demo video must show this person, not the technology. |
| **2. Technical execution** | Working code, public repo, reproducible install. Bonus for using Gemma 4's *distinctive* features: **multimodal** (Phase 2 webcam→whiteboard) and **native function calling / structured output** (already in via Ollama JSON mode; Day 5 task is to upgrade to true tool-use API). |
| **3. Clear use case** | Judges should "get it" in <30 seconds. Tagline: *"On-device AI co-teacher. No cloud. Runs on a laptop."* If a feature can't be explained that fast in a demo, defer it. |

### The "why-not-cloud-LLM" question (memorize this answer)

Judges and reviewers will repeatedly ask why this can't just use GPT-4o or Gemini. **Sensei's answer must be sharper than "open weights are nice."** Four reasons in priority order:

1. **Privacy / legal** — Many jurisdictions (and most school district IT policies) forbid sending classroom audio, especially with student voices, to third-party servers. Cloud LLMs are legally non-starters in many target environments.
2. **Cost equity** — A teacher in a low-budget district cannot afford per-token API bills for every lecture, every week, forever. Cloud AI excludes the people who need teaching support most. Gemma 4 + Ollama = one-time setup, zero marginal cost.
3. **Latency** — Real-time classroom visualization needs <2 s end-to-end. Cloud LLMs add 2–3 s of network round-trip alone, before generation. On-device is faster.
4. **Offline capability** — Rural classrooms, schools with poor connectivity, areas during disaster recovery. The "low-bandwidth environments" mentioned in the hackathon brief are real, and Gemma 4 is built for them.

This narrative goes in the README, the writeup, the demo video script, every module docstring. Repeat it.

### Submission deliverables (Day 10 checklist, expanded)

Per Kaggle rules, the submission must include:

- [ ] **Public code repository** — GitHub, with clear README, license, and install instructions a non-PhD can follow.
- [ ] **Technical writeup** — 1-2 pages: problem → solution → architecture → why Gemma 4 → impact. Save as `WRITEUP.md` in repo + paste into Kaggle form.
- [ ] **Demo video** (~3 minutes) — uploaded to YouTube (unlisted is fine), linked in submission. **This is the artifact judges spend the most time with.** The classroom shot from Day 7 lives or dies here.
- [ ] **Kaggle submission form** — final assembly of links

**Not pursued (decision 2026-05-09 evening):**
- ~~HuggingFace Spaces working demo~~ — Kaggle does not strictly require a live deployment, and Sensei's narrative is *on-device, no cloud*; hosting it on HF Spaces would actively contradict the impact thesis. The demo video shot on the user's own laptop covers "judges can see it work" without breaking the story. Re-open this only if the official rules turn out to mandate a live demo URL.

### Feature decisions, judged against this rubric

When deciding whether to build feature X before May 18, ask:
1. Does it make the **demo video** more compelling? → BUILD
2. Does it strengthen the **why-not-cloud-LLM** argument? → BUILD
3. Does it showcase Gemma 4's **distinctive capabilities** (multimodal, function calling, edge deployment)? → BUILD
4. Is it just "polish that engineers would notice"? → DEFER

Examples applied:
- ✅ Real Lucide icons → demo video looks pro → BUILD (Day 2)
- ✅ Live mic + hotkey → critical for video demo flow → BUILD (Day 3)
- ✅ Native Gemma 4 function calling → strengthens technical execution narrative → BUILD (Day 5)
- ❌ Async refactor of pipeline → engineer-only polish → DEFER
- ❌ Unit test suite → not in rubric → DEFER
- ❌ Docker container → not in rubric → DEFER
- ❌ HuggingFace Spaces hosted demo → not required by Kaggle, and contradicts the on-device narrative → DEFER unless rules change

### Useful external context

- Hackathon official page (rules, FAQ, forum): https://www.kaggle.com/competitions/gemma-4-good-hackathon/
- Gemma 4 model card and license: https://www.kaggle.com/models/google/gemma-4
- Reference architecture style for similar submissions: `johnsonhk88/Kaggle-The-Gemma-4-Good-Hackathon` on GitHub (template to crib README structure from, not code)

---

## 2. Architecture

```
🎤 Lecturer speaks
    ↓
[ core/asr.py ]   Faster-Whisper large-v3 (local, fp16)
    ↓ transcript text
[ core/llm.py ]   Gemma 4 e2b via Ollama (format="json")
    ↓ JSON
[ core/templates.py ]   Pydantic schema validation
    ↓ validated dict
[ frontend/app.py ]   Gradio UI + 4 HTML renderers
    ↓ HTML
🖥️ Visual card on screen
```

### File structure

```
sensei/
├── CLAUDE.md            ← this file
├── README.md            ← user-facing + hackathon write-up draft
├── requirements.txt
├── .gitignore
├── core/
│   ├── __init__.py      ← re-exports the public API
│   ├── asr.py           ← ASRConfig, SenseiASR
│   ├── llm.py           ← LLMConfig, SenseiLLM
│   ├── templates.py     ← 4 Pydantic schemas + TEMPLATE_REGISTRY
│   └── pipeline.py      ← SenseiPipeline (orchestrates ASR + LLM)
├── frontend/
│   ├── __init__.py
│   └── app.py           ← Gradio app + render_html() with 4 renderers
├── prompts/
│   └── classifier.txt   ← Gemma 4's instruction template
└── tests/               ← (empty, for sample_audio later)
```

### Visualization templates (curated set, expanding deliberately)

| Template | Trigger | Pydantic class | Status |
|---|---|---|---|
| `enumeration_cards` | "X has A, B, C, D" — listing parallel concepts | `EnumerationCards` | shipped |
| `comparison_table` | "A vs B differs in..." | `ComparisonTable` | shipped |
| `flow_diagram` | "First A, then B, then C" | `FlowDiagram` | shipped |
| `hierarchy_tree` | "X is divided into Y and Z, Y has..." | `HierarchyTree` | shipped |
| `swot` | strengths/weaknesses/opportunities/threats | `SWOT` | shipped 2026-05-09 |
| `pyramid` | layered linear hierarchy from apex (narrow) to base (wide) | `Pyramid` | shipped 2026-05-09 |

Why a curated set rather than free-form? LLM picking from a known list is far more reliable than LLM inventing layouts mid-lecture. **Each new template is a deliberate addition** requiring (1) Pydantic class, (2) registry entry, (3) prompt example, (4) renderer, (5) manual smoke test on representative phrases — landed one at a time, never in a batch. Beyond auto-classification, the operator UI also exposes a **template-hint dropdown** so the lecturer can force a specific template ("we're doing SWOT now"); LLM falls back to auto-pick if no hint is given.

---

## 3. ⚠️ Key decisions — DO NOT CHANGE without discussion

These are non-obvious choices made for specific reasons. Reverting them without understanding will break the project's narrative or environment.

| Decision | Why | DON'T |
|---|---|---|
| **Ollama for LLM, not transformers/bitsandbytes** | Zero-friction install for non-engineer teachers; Windows-friendly; supports `format="json"` natively. Matches the impact thesis: "any teacher can deploy Sensei." | Don't switch back to `transformers` + `bitsandbytes`. The user's Windows environment had bitsandbytes problems. Ollama works. |
| **Default model `gemma4:e2b`, not `e4b`** | VRAM budget on RTX 4080 (12 GB): Whisper large-v3 ~3 GB + Gemma 4 e2b ~7 GB = ~10 GB headroom. e4b would force CPU spillover. | Don't change default to `e4b` unless user explicitly requests, AND we downgrade ASR to medium. |
| **Faster-Whisper large-v3 for ASR** | Best Mandarin accuracy. Engineering jargon recognition critical (PID, SCADA, Modbus, etc.). Domain `initial_prompt` reduces term WER ~40-60%. | Don't downgrade to medium without user permission. |
| **JSON-mode + Pydantic post-validation (two layers)** | Layer 1 (Ollama `format="json"`) prevents invalid JSON at sampling level. Layer 2 (Pydantic) catches schema violations and gracefully degrades to `{"template": "raw"}`. | Don't remove either layer. The graceful degradation is what keeps the demo from crashing on edge cases. |
| **Curated template vocabulary, not free-form** | Stable visual identity; LLM picks from a known list. Currently 6 shipped (enumeration / comparison / flow / hierarchy / SWOT / pyramid), plus an operator hint dropdown to force a specific template. Fishbone was approved then dropped — CSS cost vs demo benefit didn't pencil out. See Section 2 for the table. | Don't let the LLM invent layouts. Each new template = Pydantic schema + registry + prompt example + renderer + smoke test, validated one at a time. |
| **Card text ≥ 24 px, key headings ≥ 36 px** | Cards are projected onto classroom screens; students sit far. Anything <20 px is unreadable past row 4. The `/display` route is pure projector view — it has to read at distance. | Don't shrink fonts to "fit more text" on a card. If content overflows, split into two cards or trim wording. Renderers must respect these minimums. |
| **Traditional Chinese as primary language** | User and target classrooms are Taiwanese. | Don't simplify to mainland Chinese. Glossary in `core/asr.py::ASRConfig.INITIAL_PROMPT` is in 繁中. |
| **HF cache at `D:\hf-cache`** | User's C drive is full. | Don't change to `~/.cache/...` (which on Windows means `C:\Users\...`). |
| **HF mirror `https://hf-mirror.com`** | Direct HuggingFace CDN was 486 KB/s for the user; mirror is ~4 MB/s in Taiwan. | Don't unset `HF_ENDPOINT`. |

---

## 4. Environment

```
OS:                 Windows 11
Hardware:           Laptop with NVIDIA RTX 4080 (12 GB VRAM)
Python:             3.12 (system Python at C:\Python\Python312-64\)
Project path:       D:\Project_CodingSimulation\PersonalHelper\sensei
Shell:              PowerShell

Environment variables (set permanently, User scope):
  HF_HOME       = D:\hf-cache
  HF_ENDPOINT   = https://hf-mirror.com

Ollama models pulled (in C:\Users\<user>\.ollama\models — may move to D later):
  gemma4:e2b   (7.2 GB)   ← default
  gemma4:e4b   (9.6 GB)   ← higher quality fallback

HF cache pulled (in D:\hf-cache):
  Systran/faster-whisper-large-v3   (~3 GB)
```

---

## 5. How to run

### Daily startup (after env is set)

```powershell
cd D:\Project_CodingSimulation\PersonalHelper\sensei

# Confirm Ollama is running (taskbar icon, or `ollama serve` in another window)
ollama list                          # should show gemma4:e2b

# Smoke test the LLM in isolation
python -m core.llm "同學，控制不是只有 PID 控制，還有最佳、類神經、非線性、強健"

# Smoke test full pipeline (text mode, no mic)
python -m core.pipeline "風機監控系統的流程是先量測振動，再特徵抽取，然後分類，最後報警"

# Launch Gradio UI
python -m frontend.app
# → open http://localhost:7860
```

### Smoke-test expectations

- `core.llm` should return JSON with `"template": "enumeration_cards"`, ~5 items
- `core.pipeline` (with the flow example) should return `"template": "flow_diagram"`
- Gradio UI: text input tab → click an example → "整理成卡片" → see styled cards on the right

---

## 6. Known issues + immediate fixes needed

### Issue #1: Gemma 4 e2b occasionally emits duplicate JSON keys
- **Symptom**: same field appears twice in output (e.g., `"icon": "brain", "icon": "brain"`)
- **Why**: `format="json"` enforces JSON validity but not key uniqueness
- **Fix**: edit `prompts/classifier.txt`, add to "嚴格輸出規則": "每個欄位在物件中只能出現一次（unique keys）"
- **Priority**: low (Python's `json.loads` accepts dup keys, takes the last; Pydantic accepts; doesn't crash)

### Issue #2: Gradio 6 API breaking changes
- **Status**: PATCHED in user's local copy via PowerShell sed
- **What changed**:
  1. `theme=` removed from `gr.Blocks(...)` constructor
  2. `show_api=False` removed from `app.launch(...)` call
- **Next time you start working**: confirm `frontend/app.py` lines around 236 and 273-277 don't have these. If they do, the patch didn't apply and Gradio will fail to start.

### Issue #3: Lucide icons not real
- **Symptom**: cards show 2-letter placeholders like "TR" (for trending-up) instead of actual icons
- **Why**: I shipped a stub `_lucide_svg()` in `frontend/app.py`
- **Fix**: replace stub with either (a) inline SVG paths from a Lucide icon dict, or (b) `<img src="https://unpkg.com/lucide-static@latest/icons/{name}.svg">` (CDN-based, simpler).
- **Priority**: HIGH — biggest visual quality win for demo video

### Issue #4: No second-screen / fullscreen mode
- **Status**: not started
- **Plan**: add a `/display` route in Gradio (or a separate FastAPI app) that shows ONLY the latest card fullscreen, no controls. The lecturer mirrors this to the projector.
- **Priority**: HIGH — needed for the demo video setup

---

## 7. Nine-day plan (calendar countdown)

```
Day 1  · 2026-05-09 (Sat)  ✅ Skeleton + Ollama backend + Gradio MVP launches
Day 2  · 2026-05-10 (Sun)  ⏳ Real Lucide icons + 2nd-screen view + prompt fixes
Day 3  · 2026-05-11 (Mon)  ⏳ Live mic mode (rolling buffer + hotkey)
Day 4  · 2026-05-12 (Tue)  ⏳ Glossary tuning per course; iterate prompt for quality
Day 5  · 2026-05-13 (Wed)  ⏳ Native Gemma 4 function-calling refactor
Day 6  · 2026-05-14 (Thu)  ⏳ Buffer day / polish UI
Day 7  · 2026-05-15 (Fri)  🎬 RECORD CLASSROOM DEMO VIDEO  ← critical day
Day 8  · 2026-05-16 (Sat)  ⏳ Edit video + write technical writeup
Day 9  · 2026-05-17 (Sun)  ⏳ Buffer / GitHub README polish / writeup final pass
Day 10 · 2026-05-18 (Mon)  📤 SUBMIT before 23:59 UTC
```

**The whole project is optimized around Day 7's video shoot.** Every feature added between now and then must be evaluable as: "does this make the demo more impressive in 3 minutes?" If no, defer.

---

## 8. Immediate next tasks (Day 2 priority order)

When the user says "let's keep going" or similar, this is the order to attack:

1. **Real Lucide icons** in `frontend/app.py::_lucide_svg()`. Recommend CDN approach (`unpkg.com/lucide-static`) — 1 line of code change, instant visual improvement.

2. **Fix prompt issue #1** (duplicate keys) in `prompts/classifier.txt`. Trivial.

3. **Add `/display` second-screen route**. Strip Gradio chrome, show only the card area, large fonts, fullscreen-friendly. Likely a simple `gr.Blocks` with just the HTML output, served on a different port or path.

4. **Test on real lecture audio**. User has access to recordings of his own lectures. Try a 30-second clip in the audio tab.

5. **Live mic mode** — only after #1-4 are stable. Rolling 30-sec buffer + hotkey to "snapshot to card." Recommend keyboard library like `keyboard` (Windows) or `pynput`. Requires `sounddevice` for streaming capture.

---

## 9. Coding conventions

- **Comments and docstrings**: English in code files; user-facing strings in 繁中
- **Type hints**: required on public functions
- **Pydantic v2 syntax**: `model_validate()`, `model_dump()`, not v1's `parse_obj` etc.
- **No emojis in code itself**, but OK in print() messages and Markdown
- **Print messages prefix**: `[Sensei ASR]`, `[Sensei LLM]`, `[Pipeline]` — easy to grep in logs
- **Don't add tests/CI/Docker/poetry/pyproject.toml** — this is a 9-day hackathon project, not enterprise. Pure `requirements.txt` + scripts.
- **Don't refactor for "cleanliness"** unless it's necessary for the next deliverable. Time is the scarcest resource.

---

## 10. What to NOT do

- ❌ Don't switch LLM backend from Ollama to transformers/llama.cpp/vLLM. Ollama is the deploy story.
- ❌ Don't let the LLM invent layouts free-form. New templates require Pydantic schema + registry + prompt example + renderer + smoke test, validated one at a time. Approved set lives in Section 2.
- ❌ Don't ship card renderers with text below the 24 px floor (36 px for key headings). See Section 3.
- ❌ Don't add tests, CI, type stubs, mypy, ruff, pre-commit, Docker, k8s, Helm, or any "professional" infrastructure. None of these help the demo video.
- ❌ Don't simplify Chinese to mainland conventions. Traditional Chinese only.
- ❌ Don't change default models (`gemma4:e2b`, `large-v3`) without checking VRAM math.
- ❌ Don't write large, generic abstractions ("BaseLLM", "LLMFactory", "PluginRegistry"). YAGNI hard for 9 days.
- ❌ Don't add async unless necessary. Gradio handles it. Premature async is a debugging tax.
- ❌ Don't auto-format the existing code with black/ruff and produce huge diffs. Touch only what you change.

---

## 11. Hackathon submission checklist

Reminder of what must exist on Day 10:

- [ ] **Public GitHub repo** with clear README + LICENSE (CC-BY 4.0 per rules §2.5.a)
- [ ] **3-minute demo video** uploaded to YouTube/Drive, linked in submission
- [ ] **Technical writeup** (1-2 pages): the problem, why Gemma 4, architecture, impact
- [ ] **Kaggle submission form** filled with all of the above

The video is the single most important artifact. It's what judges will *actually* watch. Everything else is supporting evidence.

**Note**: HuggingFace Spaces deployment was considered and dropped 2026-05-09 — see §1A. Demo video shot on the user's own laptop is the substitute.

---

## 12. Style of communication with the user

- He prefers **directness over politeness**. Don't say "Great question!" — get to the answer.
- He likes **decision tables** and **clear options**.
- He has 9+ years industry experience (ITRI, wind turbines) and active research in RAG/LLM/MCP. **Don't over-explain basics.**
- When you screw up, **own it briefly, then fix**. Don't grovel.
- He uses Windows + PowerShell. Don't give bash-only commands. Always provide PowerShell-equivalent if there's a difference.
- His current hackathon is the priority context. Other projects (WindGuard AI, MSG-IRAG paper, LLM Wiki, AutoPLC Pro) exist in his life but Sensei is the focus until 5/18.

---

*End of context. When in doubt, ask the user before changing anything in section 3 (Key decisions).*
