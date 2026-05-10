"""
Sensei · End-to-end Pipeline
================================
audio (file or array) ──► ASR ──► text ──► LLM ──► structured JSON
"""

from pathlib import Path

from .asr import SenseiASR
from .llm import SenseiLLM


class SenseiPipeline:
    """
    Loads both models once. Holds them in memory. Reuse for every utterance.
    """

    def __init__(self):
        self.asr = SenseiASR()
        self.llm = SenseiLLM()

    def process_audio(self, audio_path: str | Path, template_hint: str | None = None) -> dict:
        """Audio file → structured visualization JSON."""
        text = self.asr.transcribe(audio_path)
        print(f"[Pipeline] Transcript: {text}")
        result = self.llm.structurize(text, template_hint=template_hint)
        result["_transcript"] = text
        return result

    def process_text(self, text: str, template_hint: str | None = None) -> dict:
        """Bypass ASR — for testing without microphone."""
        result = self.llm.structurize(text, template_hint=template_hint)
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
