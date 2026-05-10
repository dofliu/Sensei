# Sensei — On-Device AI Co-Teacher

**Submission for The Gemma 4 Good Hackathon — self-nominated for Main Track + Future of Education Impact Prize + Ollama Special Technology Prize**

---

## 1. The problem

Every classroom has the same gap: the teacher *says* rich, structured ideas — *"control isn't only PID; there's also optimal, neural, nonlinear, robust control"* — but what students *see* is a static slide that took the teacher hours to build, or a whiteboard scribble. The structure lives in the teacher's head, not on the screen.

Closing this gap with cloud AI hits three walls that block the people who need help most:

1. **Privacy / legal** — Many jurisdictions (and most school district IT policies) forbid sending classroom audio, especially with student voices, to third-party servers. Cloud LLMs are legally non-starters in real K-12 environments.
2. **Cost equity** — A teacher in a low-budget district cannot afford per-token API bills for every lecture, every week, forever. Cloud AI excludes the people who need teaching support most.
3. **Latency and offline** — Real-time classroom visualization needs <2 s end-to-end. Cloud LLMs add 2–3 s of network round-trip alone, and rural / disaster-recovery / poor-connectivity classrooms have no network at all.

## 2. The solution: Sensei

Sensei is an on-device AI co-teacher. It listens to a lecturer's spoken words, classifies the intent, and renders a structured visual card on a second screen in real time — entirely on the teacher's laptop. **No audio leaves the room. No bills. ~1 second from speech to visual.**

The teacher operates Sensei from a Gradio control panel on the laptop, while the projector mirrors a separate read-only view (`/display`) that fades in each new card automatically. When a student raises a follow-up — *"oh, also robust control and gain scheduling"* — the teacher clicks **Extend last card** and the existing card grows by two items, in place, with the original four items untouched.

Six curated visualization templates cover the most common pedagogical speech patterns:

- `enumeration_cards` — listing parallel concepts
- `comparison_table` — A vs B
- `flow_diagram` — sequential steps
- `hierarchy_tree` — classifying with sub-classes
- `swot` — 2×2 strategic grid (strengths / weaknesses / opportunities / threats)
- `pyramid` — linear hierarchy from apex (narrow) to base (wide)

The set is curated, not free-form — letting the model invent layouts mid-lecture would make the classroom screen jumpy and unreadable. Each template is also exposed as a Gemma 4 tool, so template selection becomes tool selection (see §3).

## 3. Architecture

```
🎤 Teacher speaks
    │
    ▼
[ Faster-Whisper large-v3 (local, fp16) ]      ← 3 GB VRAM, Mandarin + engineering jargon
    │
    ▼ transcript
[ Gemma 4 e2b via Ollama ]                     ← 7 GB VRAM
    ├─ tool calling (primary path)              ← each template = one tool, model picks
    └─ format="json" mode (fallback path)       ← when tool-args validation fails
    │
    ▼ raw arguments / JSON
[ Pydantic schema validation ]                 ← 6 schemas, graceful degradation on failure
    │
    ▼ validated dict
[ HTML renderers + 24/36-px large-print ]
    │
    ├──▶ Gradio operator console (laptop)
    └──▶ /display fullscreen view (projector, JS-polled, fade transitions)
```

Three layers of structured-output guarantee, each catching what the previous one misses:

1. **Native function calling (primary path)** — Each visualization template is registered as a Gemma 4 tool via Ollama's `tools=` parameter, with the JSON Schema auto-derived from the Pydantic model. Template selection becomes tool selection: the model picks exactly one tool and fills its arguments. Six tools, one call per utterance.
2. **JSON-mode fallback** — `gemma4:e2b` is a 2-B-parameter model; on complex nested structures (lists of items each with three required fields), it occasionally drops a required field when filling tool arguments. When that happens, Sensei silently retries through Ollama's `format="json"` parameter, which constrains output at the sampling level — invalid JSON is unproducible. This second path uses the original prompt-driven classifier and recovers cleanly in practice.
3. **Pydantic schema validation** — Either path's output runs through Pydantic. On schema violation, Sensei degrades to a `{"template": "raw"}` fallback rather than crashing the demo. This is what keeps the classroom screen calm even on adversarial input.

The whole stack sits comfortably on a 12 GB laptop GPU (RTX 4080 in development).

## 4. Design principle: structuring engine, not oracle

Sensei deliberately does *not* ask the LLM to know the lecture topic. The lecturer remains the knowledge source; Gemma 4's job is to detect *"this is a parallel-list utterance"* or *"this is A vs B"* and slot the spoken content into the right template. The model classifies and structures — it does not author content from its weights.

This single design decision explains a lot of Sensei's other choices:

- It justifies using a **small model** (`gemma4:e2b`). We don't need encyclopedic recall; we need reliable template selection and slot filling. A 2-B-parameter model on a laptop GPU is *more than enough* for that, and it makes the entire on-device deploy story possible.
- It makes the **on-device privacy story real**. We aren't trying to be ChatGPT-on-the-edge; we're trying to be a *layout engine* on the edge. The smaller demand means smaller model, means it actually runs locally.
- It lets us be honest in the demo: when Sensei produces a great card, that's because the *teacher* said something well-structured and Gemma 4 saw it; we are not pretending the model is an oracle.

This is a feature, not a limit. Sensei is a tool for teachers who already have the content; it surfaces their structure without asking them to switch to an LLM-driven tool that would take over their voice.

## 5. Why Gemma 4 specifically

The judges will ask "why not GPT-4o or Gemini?". Sensei's answer is sharper than "open weights are nice":

| Reason | What it buys for Sensei |
|---|---|
| **Open weights, classroom-deployable** | A teacher can deploy locally with no per-call fee and ship the install forward. The privacy/cost story is real, not aspirational. |
| **Edge-friendly sizes match the structuring task** | `e2b` (~7 GB) coexists with Whisper large-v3 on a single 12 GB laptop GPU. Because we ask Gemma 4 only to *structure* (not to know), `e2b` is genuinely sufficient — exactly the use case the smaller variant was built for. |
| **Native structured output — two distinct mechanisms** | Sensei uses both of Gemma 4's structured-output paths through Ollama: (1) **native function calling** (`tools=[...]`) for primary template selection — each template is a tool, the model picks one and fills its arguments; (2) **JSON-mode** (`format="json"`) as a sampling-level fallback when tool-arg filling drops a field. Pydantic is the third safety net. We deliberately keep the dual-path design rather than picking one — small models benefit from belt-and-braces. |
| **Multilingual translation — same model, eight languages** | Switching the projector language toggle (中/EN/日/한국어/Tiếng Việt/Bahasa Indonesia/Español/Français) issues a translate-this-card prompt to the *same* Gemma 4 e2b. Translations are cached per card in the history JSON. One small model covers eight projection languages — the small-model-is-enough thesis pays off here too. |

### Why we kept Whisper, not Gemma 4 audio

Gemma 4 e2b is multimodal — it can transcribe audio directly. We evaluated this and **deliberately kept Whisper large-v3 in the ASR slot** for engineering reasons that are themselves part of the submission's argument:

- Whisper is specialized: **1.5 B parameters dedicated to ASR**, trained on 680k+ hours of multilingual audio. Gemma 4 e2b's 2 B parameters are split across text, vision, and audio capabilities — each modality necessarily gets less specialization.
- For Mandarin + English engineering jargon code-switching (Sensei's primary domain), Whisper's `INITIAL_PROMPT` glossary mechanism (PID, SCADA, Modbus, Simulink…) drops term-WER by 40–60 %. Gemma 4 audio has no equivalent affordance.
- A noisy transcript poisons the structuring layer downstream. The marginal gain from "100 % Gemma 4 pipeline" doesn't outweigh the demo-breaking risk of mistranscribed technical terms.

This is on-device pragmatism: **best tool for each subtask**, not "showcase Gemma 4 in every role". Whisper carries ASR; Gemma 4 carries everything else (template classification, slot filling, translation, summarization, suggestion generation, salvage). The result is structurally cleaner and operationally more reliable.

## 6. Why Ollama (Special Technology Track positioning)

Sensei's deploy story rests entirely on Ollama, and that is a deliberate technical choice — not a convenience:

- **Zero-friction install for non-engineers** — the impact thesis ("any teacher anywhere") collapses if the install requires a Python ML environment, CUDA driver matching, and quantization config. With Ollama, it is `ollama pull gemma4:e2b` and done.
- **Native JSON mode + tool calling** — Ollama exposes both Gemma 4 capabilities through the same client: `format="json"` constrains output at the sampling level; `tools=[...]` lets us register each Pydantic schema as a callable tool. Sensei uses tool calling as the primary path, JSON mode as the fallback — both produced by Gemma 4, both natively supported by Ollama, no prompt-engineering hacks required.
- **Automatic VRAM management** — Whisper and Gemma 4 coexist gracefully on a 12 GB laptop because Ollama swaps weights in/out of GPU memory under contention.
- **llama.cpp under the hood** — production-grade edge inference, not a hack.

Sensei is the kind of project the Ollama Special Prize description points at directly: *"the best project that utilizes and showcases the capabilities of Gemma 4 running locally via Ollama."*

## 7. Why Future of Education (Impact Track positioning)

The Impact prize description says: *"Reimagine the learning journey by building multi-tool agents that adapt to the individual and empower the educator through seamless integration."*

Sensei reads this brief literally:

- **Adapts to the individual** — the lecturer can extend any card on the fly, force a specific template, hint domain vocabulary; the system bends around the teacher rather than the other way round.
- **Empowers the educator** — Sensei does the slide-design labor that teachers in under-resourced classrooms cannot afford the time for. It does it during the lecture, not the night before.
- **Seamless integration** — the teacher's existing equipment (a laptop + a projector) becomes a co-teaching rig with no new hardware, no IT department conversation, no monthly subscription.

The named beneficiary is concrete: **the under-resourced classroom teacher** in any jurisdiction where cloud audio is not legally available, in any budget where cloud AI is not financially available, in any building where bandwidth is not reliably available.

## 8. Roadmap and honest limits

What ships by Day 10:

- Live microphone with toggle hotkey (F8 + Ctrl+Space; presenter-pen friendly)
- Two additional visualization templates landed: SWOT (2×2) and linear pyramid (fishbone deferred — CSS cost vs demo benefit didn't pencil out)
- Theme switching for different classroom lighting (dark / light / paper); paper editorial type pairing (Playfair Display + Geist + JetBrains Mono)
- **Native Gemma 4 function-calling** as the primary template-selection path, with JSON-mode as a silent fallback when small-model tool-arg filling drops fields. Template tools are auto-derived from Pydantic schemas — no hand-written tool spec
- **Multilingual projection** — the projector view re-renders in any of 8 languages on demand, all via the same on-device Gemma 4
- **Lenient salvage** — when Gemma 4 e2b drops a required field on nested arrays, Sensei fills safe placeholders (icon → `circle`, desc → `""`) rather than crashing the demo. Logged transparently as `_salvaged: true` in the history JSON
- Real classroom demo video shot at NCUT

### What we deliberately chose **not** to build

These were evaluated end-to-end and rejected for product reasons. Documenting them is part of the submission — it shows the choices behind the working system.

- **Multimodal whiteboard capture** — Gemma 4's vision capability tempted us, and a "snap the whiteboard, get a structured card" demo would have been visually impressive. We walked it through and rejected it on two grounds:
  - **Hardware contradicts the thesis.** Sensei's pitch is "the teacher's existing equipment becomes a co-teaching rig — no new hardware, no IT department conversation." A whiteboard-camera workflow requires either a second webcam aimed at the board, or the lecturer physically lifting the laptop to point it at the board. Either breaks the universal-deploy story we sell.
  - **VRAM contention with Whisper.** Running Gemma 4 vision concurrent with Whisper large-v3 on a 12 GB laptop GPU forces a model swap (3–5 s of latency added to every "snap"), which kills the real-time feel that makes Sensei work in the first place.

  The capability is **not deleted**, only deferred. A future deployment on hardware that already includes a board camera (Smartboard, document camera, classroom PTZ camera) can enable it via a config flag without re-architecting Sensei. We chose alignment with the impact thesis over a demo-only feature flourish.

- **Gemma 4 audio replacing Whisper** — same logic in §5: best tool for each subtask. Multimodal cosplay isn't worth the demo-time transcription regression.

- **Free-form (non-templated) layouts** — letting Gemma 4 invent layouts every utterance was a tempting "let the model show off" move, but classroom screens go jumpy and unreadable when every card looks different. Six curated templates beat infinite layouts for pedagogy. Same reasoning behind dropping the fishbone diagram: visual cost outweighed teaching benefit.

What is honest to flag:

- **Whisper accuracy on heavy code-switching** (Mandarin ↔ English engineering terms) is good but not perfect. The domain `initial_prompt` mitigates this; further glossary expansion is iterative.
- **Single-language LLM prompts**. Sensei targets Traditional Chinese classrooms first; English / other-language prompts are a Day-1A-onward extension.
- **No persistent multi-user mode**. Each teacher runs their own local instance — by design (privacy), but means cross-classroom analytics are not in scope.

## 9. License

This work is licensed under **CC-BY 4.0** (per hackathon rules §1.6 + §2.5.a). Bundled model weights retain their upstream licenses (Gemma license for Gemma 4; MIT for Whisper).

---

*Sensei · 先生 — built so any teacher, anywhere, can have a co-teacher.*

*Project lead: Liu Jui-Hung (劉瑞弘), Associate Professor, Department of Intelligent Automation Engineering, National Chin-Yi University of Technology, Taiwan · DOF Lab*
