"""
Sensei · End-to-end Pipeline
================================
audio (file or array) ──► ASR ──► text ──► LLM ──► structured JSON
"""

import re
import time
from pathlib import Path

from .asr import SenseiASR
from .glossary import load_glossary
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


# ── Continuous-listening gate (PROPOSAL B1) ─────────────────────────
# Two layers. This is the rule layer, which costs nothing; the model layer is
# the no_card tool in core/llm.py. Without a gate every sentence becomes a
# card and the projector strobes.
#
# These two numbers are the ones to tune after a real lecture. They live here,
# together, on purpose — do not scatter them into call sites.
GATE_MIN_CONTENT = 15    # below this "content length", skip without asking the LLM
LATIN_WORD_WEIGHT = 2    # one English word ≈ two Chinese characters of content

_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
_LATIN_WORD = re.compile(r"[A-Za-z0-9]+")


def content_length(text: str) -> int:
    """Rough "how much was actually said", comparable across zh and en.

    Chinese characters count 1 each; a run of Latin letters/digits counts
    LATIN_WORD_WEIGHT, because 15 Chinese characters and 15 English words are
    not remotely the same amount of lecture.
    """
    if not text:
        return 0
    return (len(_CJK.findall(text))
            + LATIN_WORD_WEIGHT * len(_LATIN_WORD.findall(text)))


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

    # ── Course settings (operator UI, PROPOSAL B2) ─────────────────────
    def set_glossary(self, glossary_id: str) -> bool:
        """Swap the Whisper initial_prompt to glossaries/<id>.<lang>.txt."""
        g = load_glossary(glossary_id)
        if g is None:
            print(f"[Pipeline] unknown glossary '{glossary_id}', keeping current", flush=True)
            return False
        self.asr.set_glossary(g.text, label=g.title)
        return True

    def set_lecture_language(self, lang: str) -> None:
        """'zh' | 'en' | 'auto'. Drives Whisper's language and the card language
        Gemma 4 writes in (English lectures get English cards, no translation)."""
        self.asr.set_language(lang)
        self.llm.set_output_lang("en" if lang == "en" else "zh")

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

    # ── Continuous listening (PROPOSAL B1) ─────────────────────────────
    def process_utterance_audio(self, audio, sample_rate: int = 16000,
                                template_hint: str | None = None) -> dict:
        """One VAD-segmented float32 mono buffer → card or recorded skip.
        This is what the continuous listener's worker calls.

        ASR and LLM are timed separately. When the queue starts dropping, the
        only useful question is which of the two is eating the budget, and
        guessing at it is how you tune the wrong constant.
        """
        t0 = time.perf_counter()
        text = self.asr.transcribe_array(audio, sample_rate=sample_rate)
        asr_ms = int((time.perf_counter() - t0) * 1000)
        audio_s = round(len(audio) / sample_rate, 1)
        print(f"[Pipeline] Utterance ({audio_s}s audio, ASR {asr_ms} ms): {text}",
              flush=True)
        result = self.process_utterance(text, template_hint=template_hint)
        result["_asr_ms"] = asr_ms
        result["_audio_s"] = audio_s
        return result

    def process_utterance(self, text: str, template_hint: str | None = None) -> dict:
        """One VAD-segmented utterance → a card, or a recorded skip.

        Same as process_text but with the two-layer gate in front. The result
        always carries `_gate` so history (and the C2 bench) can answer
        "how often did we skip, and who decided" without re-running anything.

        `_gate` values:
          quiz-phrase  the teacher said a wake phrase — always a card
          operator     an explicit template was picked in the UI
          too-short    rule layer skipped it, no LLM call
          no-card      the model chose the no_card tool
          card         the model produced a card
          raw          all four output layers missed (still shown, degraded)
        """
        text = (text or "").strip()
        hint = self._resolve_hint(text, template_hint)
        if hint is not None:
            gate = "quiz-phrase" if template_hint is None else "operator"
            t0 = time.perf_counter()
            result = self.llm.structurize(text, template_hint=hint)
            result["_llm_ms"] = int((time.perf_counter() - t0) * 1000)
            result["_gate"] = gate
            result["_transcript"] = text
            return result

        n = content_length(text)
        if n < GATE_MIN_CONTENT:
            print(f"[Pipeline] gate: skipped (content={n} < {GATE_MIN_CONTENT}) {text!r}", flush=True)
            # The rule layer is the only path that costs no LLM call at all,
            # which is exactly why raising GATE_MIN_CONTENT is the first lever
            # to reach for when the queue starts dropping.
            return {"template": "no_card", "reason": "too short", "_llm_ms": 0,
                    "_gate": "too-short", "_content": n, "_transcript": text}

        t0 = time.perf_counter()
        result = self.llm.structurize(text, allow_no_card=True)
        result["_llm_ms"] = int((time.perf_counter() - t0) * 1000)
        if result.get("template") == "no_card":
            print(f"[Pipeline] gate: model skipped ({result.get('reason', '')}) {text!r}", flush=True)
            result["_gate"] = "no-card"
        else:
            result["_gate"] = "raw" if result.get("template") == "raw" else "card"
        result["_content"] = n
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
