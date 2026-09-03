# Contributing to Sensei

Thanks for taking a look. Sensei was built for **The Gemma 4 Good Hackathon
(Kaggle × Google DeepMind, 2026)** by [Liu Jui-Hung](https://github.com/dofliu)
at DOF Lab, NCUT, Taiwan, and is now developed for real weekly classroom use
(see [PROJECT_ENHANCEMENT_PROPOSAL.md](PROJECT_ENHANCEMENT_PROPOSAL.md)). The
codebase is intentionally small (~3,500 lines) so you can read the whole thing
in a sitting before contributing.

## Quick orientation

```
sensei/
├── core/
│   ├── asr.py        Faster-Whisper wrapper (language + glossary switchable)
│   ├── glossary.py   Loads glossaries/*.txt into Whisper initial_prompts
│   ├── llm.py        Gemma 4 via Ollama: tool calling + JSON mode + salvage
│   ├── templates.py  Seven Pydantic schemas (the visual templates)
│   ├── pipeline.py   ASR → LLM glue + quiz spoken-trigger guard
│   └── live_mic.py   Server-side microphone capture (toggle via F8)
├── frontend/
│   ├── app.py        Gradio operator console: layout, handlers, history
│   ├── renderers.py  THEMES + the 7 card renderers (dict → HTML)
│   ├── i18n.py       Operator-UI strings (zh / en)
│   └── display.py    /display projector page + SSE feed + FastAPI mount
├── glossaries/       One ASR glossary per course; add a .txt, no code change
├── prompts/
│   ├── classifier.txt  Template selection + slot filling
│   └── extender.txt    Card extension (locked-template mode)
├── PROJECT_ENHANCEMENT_PROPOSAL.md   Post-hackathon roadmap (start here)
├── WRITEUP.md       The hackathon submission writeup (archived)
└── DEMO_SCRIPT.md   The 3-minute demo video shoot plan (archived)
```

Start at `WRITEUP.md` for *why*, `PROJECT_ENHANCEMENT_PROPOSAL.md` for *where
it is going*, `frontend/app.py` for *how it wires together*, and `core/llm.py`
for *how Gemma 4 is used*.

## Development setup

See [README · Quick start](README.md#quick-start) for prereqs (Ollama, PyTorch,
Faster-Whisper). Then:

```powershell
pip install -r requirements.txt
.\start_sensei.ps1          # checks Ollama + model, starts the app, opens both tabs
# or: python -m frontend.app
# Operator:  http://localhost:7860/
# Projector: http://localhost:7860/display  (F11 for fullscreen)
```

Smoke test the LLM in isolation without launching the UI:

```powershell
python -m core.llm "同學, 控制不只 PID, 還有最佳、神經、非線性、強健"
```

## What kind of contributions are welcome

In rough order of usefulness:

1. **Real classroom feedback** — file an issue with the lecture domain you tried,
   the transcript Sensei produced, and what looked off. Concrete failure cases
   are gold for prompt and glossary tuning.
2. **A glossary for your course** — copy `glossaries/_template.txt` to
   `glossaries/<your_course>.zh.txt` (or `.en.txt`), fill in the acronyms
   Whisper mishears in your field (medical, legal, finance…), and open a PR.
   No Python involved; see `glossaries/README.md` for the format.
3. **New visualization templates** — but please open an issue first to discuss
   *why* the existing seven don't cover the case. Each new template needs:
   Pydantic schema (`core/templates.py`) → registry entry → tool description
   (`core/llm.py`) → prompt example (`prompts/classifier.txt`) → renderer
   (`frontend/renderers.py`) → dropdown label (`frontend/i18n.py`) → smoke test
   on a representative transcript. Validate before opening a PR.
4. **Translations** — Sensei's UI ships in zh + en. If you want to add another
   operator-UI language, extend `UI_TEXTS` in `frontend/i18n.py` and submit a PR.
   The card-content language list (currently 8 languages via Gemma 4) is
   separate and lives in `_list_languages()` and `core/llm.py::TRANSLATION_TARGETS`.
5. **Demo videos** in your own classroom — share them, we'd love to see Sensei
   in different teaching contexts.

## What I am NOT looking for

- **Framework rewrites** (React front-end, async everywhere, plugin systems) —
  the roadmap in the proposal is deliberately incremental.
- **Adding cloud LLM fallbacks** — the on-device principle is load-bearing.
  See `WRITEUP.md` §4 ("structuring engine, not oracle") and §5 (why we kept
  Whisper instead of Gemma 4 audio).
- **Adding an 8th template just because** — see §8 of the writeup. Curated
  vocabulary is the design.
- **Vision / multimodal whiteboard capture** — evaluated and deferred. See
  WRITEUP §8 "What we deliberately chose not to build". A future deployment on
  hardware that already has a board camera can re-enable it.

## Code style

- **Python 3.12**, type hints on public functions, Pydantic v2 syntax.
- **Comments and docstrings**: English in code; user-facing strings in 繁中
  (Traditional Chinese) with English translations in `UI_TEXTS`.
- **No unit-test suite / CI / Docker** — pure `requirements.txt` + scripts.
  An evaluation set under `bench/` (labelled utterances → template accuracy)
  is welcome; see the proposal, Phase C.
- **No async** unless necessary. Gradio + FastAPI handle concurrency.

## License

Sensei is released under [CC-BY 4.0](LICENSE) per hackathon rules §1.6 + §2.5.a.
By contributing, you agree your contribution is licensed under the same terms.

Bundled / runtime models (Gemma 4, Whisper) retain their upstream licenses.

## Communication

- **Issues** for bugs, feature requests, classroom test reports
- **PRs** welcome; small focused diffs > big refactors
- **moredof@gmail.com** for hackathon-time questions where an issue thread isn't
  the right venue

Thanks for reading this far. Sensei was built so any teacher, anywhere, can have
a co-teacher — contributions that move that mission forward are most welcome.
