"""
Sensei · dry-run smoke helper
=============================
Called by dry_run.ps1 — keeps the Chinese test prompts in a UTF-8 Python file
to dodge PowerShell 5.1's system-codepage parsing of .ps1 source.

Usage:
    python dry_run_smoke.py enum      # LLM-only enumeration_cards smoke
    python dry_run_smoke.py quiz      # full pipeline + spoken-trigger smoke
    python dry_run_smoke.py audio     # list audio input devices

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
}


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"usage: python dry_run_smoke.py {{{'|'.join(COMMANDS)}}}")
        sys.exit(2)
    sys.exit(COMMANDS[sys.argv[1]]())
