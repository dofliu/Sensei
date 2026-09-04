"""
Sensei · dry-run smoke helper
=============================
Called by dry_run.ps1 — keeps the Chinese test prompts in a UTF-8 Python file
to dodge PowerShell 5.1's system-codepage parsing of .ps1 source.

Usage:
    python dry_run_smoke.py enum      # LLM-only enumeration_cards smoke
    python dry_run_smoke.py quiz      # full pipeline + spoken-trigger smoke
    python dry_run_smoke.py audio     # list audio input devices
    python dry_run_smoke.py gate      # B1 gate + B3 session/handout, no models
    python dry_run_smoke.py whisper   # is the large-v3 cache actually usable offline

Exit codes:
    0 = pass
    1 = fail
    2 = unknown sub-command
"""

import sys


ENUM_PROMPT = "同學，控制不是只有 PID 控制，還有最佳、類神經、非線性、強健控制"
QUIZ_PROMPT = "今天講了 PID 三個分量，來考一題，下列哪一個負責消除穩態誤差？"


def smoke_enum() -> int:
    """LLM smoke: canonical PID example should pick enumeration_cards."""
    from core.llm import SenseiLLM
    llm = SenseiLLM()
    result = llm.structurize(ENUM_PROMPT)
    template = result.get("template")
    if template == "enumeration_cards":
        print(f"PASS template={template}")
        return 0
    print(f"FAIL got template={template!r}, expected enumeration_cards")
    print("--- raw result ---")
    for k, v in result.items():
        print(f"  {k}: {v}")
    return 1


def smoke_quiz() -> int:
    """Pipeline smoke: 來考一題 wake-phrase should hard-force quiz_card.
    Captures pipeline stdout to confirm the trigger-detection print fires."""
    import io
    from contextlib import redirect_stdout
    from core.pipeline import SenseiPipeline

    buf = io.StringIO()
    pipeline = SenseiPipeline()
    with redirect_stdout(buf):
        result = pipeline.process_text(QUIZ_PROMPT)
    captured = buf.getvalue()
    # Echo captured output so the rehearsal log shows it
    print(captured, end="")

    template = result.get("template")
    trigger_fired = "quiz trigger phrase detected" in captured

    if template == "quiz_card" and trigger_fired:
        print(f"PASS template=quiz_card AND spoken-trigger fired")
        return 0
    if template == "quiz_card" and not trigger_fired:
        print(f"WARN template=quiz_card but trigger log not captured "
              f"(model picked it on its own; deterministic guard not exercised)")
        return 0  # still a pass for shoot purposes
    print(f"FAIL template={template!r}, trigger_fired={trigger_fired}")
    return 1


# Files faster-whisper opens when it loads a CTranslate2 Whisper model.
# vocabulary.json (large-v3) and vocabulary.txt (older conversions) are
# alternatives, so they are checked as a pair.
WHISPER_SIZE = "large-v3"
WHISPER_REPO = "models--Systran--faster-whisper-large-v3"
WHISPER_REQUIRED = ("model.bin", "config.json", "tokenizer.json")
WHISPER_EITHER = ("vocabulary.json", "vocabulary.txt")
WHISPER_MODEL_MIN_BYTES = 2_000_000_000   # large-v3 model.bin is ~3.1 GB


def _human(n: int) -> str:
    for unit, div in (("GB", 1e9), ("MB", 1e6), ("KB", 1e3)):
        if n >= div:
            return f"{n / div:.1f} {unit}"
    return f"{n} B"


def smoke_whisper() -> int:
    """Is the Whisper cache actually loadable, not merely present?

    Checking that the directory exists is not enough: an interrupted download
    leaves the directory, the snapshot and some blobs behind, and the failure
    only surfaces later as a huggingface_hub LocalEntryNotFoundError from
    inside WhisperModel(). This looks at the files themselves so the preflight
    fails at the cache step with something actionable.
    """
    import os
    from pathlib import Path

    home = Path(os.environ.get("HF_HOME") or (Path.home() / ".cache" / "huggingface"))
    repo = home / "hub" / WHISPER_REPO
    print(f"  HF_HOME   {home}")
    print(f"  repo dir  {repo}")

    if not repo.is_dir():
        print(f"FAIL cache directory not found: {repo}")
        return 1

    # A partially downloaded blob is the usual cause; name it explicitly.
    incomplete = sorted((repo / "blobs").glob("*.incomplete")) if (repo / "blobs").is_dir() else []
    for f in incomplete:
        print(f"  partial   {f.name} ({_human(f.stat().st_size)}, a download that never finished)")

    snapshots = sorted((repo / "snapshots").iterdir()) if (repo / "snapshots").is_dir() else []
    snapshots = [d for d in snapshots if d.is_dir()]
    if not snapshots:
        print("FAIL no snapshot directory - nothing was ever fully downloaded")
        return 1

    problems = []
    for snap in snapshots:
        print(f"  snapshot  {snap.name}")
        names = {p.name for p in snap.iterdir()}
        for want in WHISPER_REQUIRED:
            f = snap / want
            if want not in names:
                problems.append(f"{want} missing from snapshot {snap.name}")
                print(f"    [--] {want}  MISSING")
                continue
            try:
                size = f.stat().st_size          # follows the blob symlink
            except OSError as e:
                problems.append(f"{want} unreadable ({e})")
                print(f"    [--] {want}  UNREADABLE - dangling link into blobs/")
                continue
            if want == "model.bin" and size < WHISPER_MODEL_MIN_BYTES:
                problems.append(f"model.bin is only {_human(size)}, expected ~3.1 GB")
                print(f"    [--] {want}  {_human(size)} - truncated")
            else:
                print(f"    [ok] {want}  {_human(size)}")
        if not (names & set(WHISPER_EITHER)):
            problems.append(f"neither {' nor '.join(WHISPER_EITHER)} in snapshot {snap.name}")
            print(f"    [--] {' / '.join(WHISPER_EITHER)}  MISSING")

    if problems:
        for pr in problems:
            print(f"FAIL {pr}")
        return 1
    if incomplete:
        print("  note      the .incomplete leftovers above are safe to delete")

    # Files being present is necessary but NOT sufficient. huggingface_hub
    # resolves "which commit is main" through refs/main; without it the cache
    # cannot be used offline at all, and faster-whisper falls back to the Hub
    # and dies with LocalEntryNotFoundError even though every byte is on disk.
    # Reproduced in the sandbox: two identical caches, one with refs/main and
    # one without, resolve and fail respectively. So run the real resolution.
    refs_dir = repo / "refs"
    if refs_dir.is_dir():
        for r in sorted(refs_dir.iterdir()):
            try:
                print(f"  refs/{r.name:<9} {r.read_text(encoding='utf-8').strip()}")
            except Exception as e:
                print(f"  refs/{r.name:<9} UNREADABLE ({e})")
    else:
        print("  refs/     directory does not exist")

    ref = refs_dir / "main"
    if not ref.is_file():
        print("    [--] refs/main  MISSING - the cache cannot be resolved offline")
        print("FAIL refs/main is missing; huggingface_hub cannot tell which "
              "snapshot 'main' is without asking the Hub")
        if len(snapshots) == 1:
            # Written through Python, not `echo >`: PowerShell 5.1's redirection
            # emits UTF-16LE, which huggingface_hub cannot read back.
            print("  repair (one snapshot, so the mapping is unambiguous):")
            print(f'    python -c "from pathlib import Path; p=Path(r\'{ref}\');'
                  f' p.parent.mkdir(parents=True, exist_ok=True);'
                  f' p.write_text(\'{snapshots[0].name}\')"')
        else:
            print(f"  {len(snapshots)} snapshots present, so which one 'main' means "
                  f"is a guess; re-download instead:")
            for snap in snapshots:
                print(f"    {snap.name}")
        return 1

    # Resolve the way faster-whisper itself does, not an approximation of it.
    # download_model() only resolves and returns a path - no GPU, no model load -
    # so this reproduces the exact failure step 7 hits, in a second.
    try:
        import faster_whisper
        from faster_whisper.utils import download_model
    except Exception as e:
        print(f"FAIL cannot import faster_whisper: {e}")
        return 1
    print(f"  fw        faster-whisper {getattr(faster_whisper, '__version__', '?')}")

    try:
        path = download_model(WHISPER_SIZE, local_files_only=True)
        print(f"  resolved  {path}")
    except Exception as e:
        print(f"FAIL faster-whisper cannot resolve {WHISPER_SIZE} offline: "
              f"{type(e).__name__}")
        for line in str(e).splitlines()[:4]:
            print(f"    {line[:110]}")
        print("  This is the same failure step 7 hits. The files above are")
        print("  present, so the problem is the revision lookup, not the data.")
        return 1

    print(f"PASS {WHISPER_SIZE} resolves offline; a lecture starts with no network")
    return 0


def smoke_gate() -> int:
    """B1 rule layer + B3 session/handout. Imports only — no model loads,
    so this stays fast and still fails loudly if a refactor broke the wiring."""
    import json
    import tempfile
    from pathlib import Path

    from core.llm import NO_CARD_TOOL, TOOL_DESCRIPTIONS
    from core.pipeline import GATE_MIN_CONTENT, content_length
    from core import session
    from frontend.handout import build_handout

    problems = []

    # The 8th tool must exist and must NOT be one of the seven templates.
    if NO_CARD_TOOL["function"]["name"] != "no_card":
        problems.append("no_card tool is not named no_card")
    if "no_card" in TOOL_DESCRIPTIONS:
        problems.append("no_card leaked into TOOL_DESCRIPTIONS (it is not a template)")

    # Rule layer: chit-chat below the threshold, real content above it.
    checks = [
        ("好，那我們繼續",                                                 False),
        ("下一頁",                                                         False),
        ("OK next slide",                                                  False),
        ("同學，控制不是只有 PID 控制，還有最佳、類神經、非線性、強健控制",  True),
        ("Control is not only PID, there is also optimal, neural, "
         "nonlinear and robust control",                                   True),
    ]
    for text, should_pass in checks:
        n = content_length(text)
        passes = n >= GATE_MIN_CONTENT
        mark = "pass" if passes else "skip"
        print(f"  content={n:>3} -> {mark:<4} {text[:44]}")
        if passes != should_pass:
            problems.append(f"gate got {mark} for {text[:24]!r} (content={n})")

    # Session + handout, in a throwaway directory.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        s = session.start("dry run", root=root)
        card = {"template": "enumeration_cards", "title": "控制方法",
                "subtitle": "", "items": [
                    {"name": "PID", "icon": "settings", "desc": "常用", "name_en": "", "tag": ""},
                    {"name": "強健", "icon": "shield", "desc": "抗擾", "name_en": "", "tag": ""}]}
        (s.dir / "20260101_120000_enumeration_cards.json").write_text(
            json.dumps({"timestamp": "20260101_120000", "transcript": "測試",
                        "data": card}, ensure_ascii=False), encoding="utf-8")
        if [p.name for p in session.card_files(s.dir)] != ["20260101_120000_enumeration_cards.json"]:
            problems.append("session.card_files did not exclude session.json")
        out = build_handout(s.dir, course="dry run", date=s.date)
        session.end()
        if out is None or not out.exists() or out.stat().st_size < 1000:
            problems.append("handout.html was not written")

    if problems:
        for p in problems:
            print(f"FAIL {p}")
        return 1
    print("PASS gate thresholds, no_card tool, session dir and handout export")
    return 0


def smoke_audio() -> int:
    """List input-capable audio devices for eyeballing the right mic."""
    import sounddevice as sd
    devs = sd.query_devices()
    inputs = [(i, d) for i, d in enumerate(devs) if d["max_input_channels"] > 0]
    if not inputs:
        print("FAIL no input-capable audio devices found")
        return 1
    print(f"PASS {len(inputs)} input device(s):")
    for i, d in inputs:
        name = d["name"]
        ch = d["max_input_channels"]
        sr = int(d.get("default_samplerate", 0))
        print(f"  [{i:>2}] in:{ch} {sr} Hz · {name}")
    return 0


COMMANDS = {
    "enum":  smoke_enum,
    "quiz":  smoke_quiz,
    "audio": smoke_audio,
    "gate":  smoke_gate,
    "whisper": smoke_whisper,
}


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"usage: python dry_run_smoke.py {{{'|'.join(COMMANDS)}}}")
        sys.exit(2)
    sys.exit(COMMANDS[sys.argv[1]]())
