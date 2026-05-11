"""
Sensei · End-to-end Pipeline
================================
audio (file or array) ──► ASR ──► text ──► LLM ──► structured JSON
"""

from pathlib import Path

from .asr import SenseiASR
from .llm import SenseiLLM


# Spoken phrases that hard-trigger quiz_card, bypassing the LLM's template
# classification. The model sometimes picks enumeration_cards or another
# template even when "考一題" is in the transcript — this substring guard makes
# the in-class demo flow deterministic: if the teacher says one of these, a
# quiz card WILL be generated, no exceptions.
#
# Only fires when the operator has NOT explicitly picked a template from the
# UI dropdown (template_hint is None). An explicit operator choice always wins.
QUIZ_TRIGGER_PHRASES = (
    "來考一題", "來考大家", "考一題", "考考大家", "出一題", "出個題",
    "考一下", "來測一下", "小測一下", "小測驗", "隨堂測驗",
    "來個 quiz", "來個小考", "來個小測",
    "quick check", "quick quiz", "pop quiz",
)


def _detect_quiz_trigger(text: str) -> bool:
    """True if the transcript contains a quiz wake-phrase. Case-insensitive."""
    if not text:
        return False
    lowered = text.lower()
    return any(p.lower() in lowered for p in QUIZ_TRIGGER_PHRASES)


class SenseiPipeline:
    """
    Loads both models once. Holds them in memory. Reuse for every utterance.
    """

    def __init__(self):
        self.asr = SenseiASR()
        self.llm = SenseiLLM()

    def _resolve_hint(self, text: str, template_hint: str | None) -> str | None:
        """Apply spoken-trigger overrides before handing off to the LLM."""
        if template_hint is None and _detect_quiz_trigger(text):
            print("[Pipeline] quiz trigger phrase detected → forcing template_hint=quiz_card", flush=True)
            return "quiz_card"
        return template_hint

    def process_audio(self, audio_path: str | Path, template_hint: str | None = None) -> dict:
        """Audio file → structured visualization JSON."""
        text = self.asr.transcribe(audio_path)
        print(f"[Pipeline] Transcript: {text}")
        hint = self._resolve_hint(text, template_hint)
        result = self.llm.structurize(text, template_hint=hint)
        result["_transcript"] = text
        return result

    def process_text(self, text: str, template_hint: str | None = None) -> dict:
        """Bypass ASR — for testing without microphone."""
        hint = self._resolve_hint(text, template_hint)
        result = self.llm.structurize(text, template_hint=hint)
        result["_transcript"] = text
        return result

    def extend_with_text(self, base_data: dict, new_text: str) -> dict:
        """延伸：用文字補充內容到既有卡片。"""
        result = self.llm.extend(base_data, new_text)
        result["_transcript"] = new_text
        return result

    def extend_with_audio(self, base_data: dict, audio_path: str | Path) -> dict:
        """延伸：用音檔補充內容到既有卡片。"""
        text = self.asr.transcribe(audio_path)
        print(f"[Pipeline] Extend transcript: {text}")
        result = self.llm.extend(base_data, text)
        result["_transcript"] = text
        return result


if __name__ == "__main__":
    import sys
    import json

    pipeline = SenseiPipeline()

    if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
        result = pipeline.process_audio(sys.argv[1])
    else:
        text = " ".join(sys.argv[1:]) or (
            "同學，我們的控制不是只有 PID 控制，"
            "其實還有最佳、類神經、非線性、強健控制等等"
        )
        result = pipeline.process_text(text)

    print("\n--- Result ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))
