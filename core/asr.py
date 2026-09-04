"""
Sensei · ASR Module
================================
Faster-Whisper wrapper for real-time Traditional Chinese speech recognition.

Why Faster-Whisper:
- 4-5x faster than openai/whisper, same accuracy
- Built-in VAD (voice activity detection) cuts silence
- INT8/float16 quantization fits alongside Gemma 4 on RTX 4080 (12GB)

Why the model loads offline-first:
- Sensei's whole pitch includes "works in a classroom with no connectivity".
  faster-whisper's default is to ask the Hub which commit `main` points at on
  every single startup, so a laptop with the model already cached still fails
  to start when the network (or the hf-mirror) is unreachable. We try the
  local cache first and only touch the network when that genuinely misses.

Why custom initial_prompt:
- Whisper severely under-recognizes engineering jargon by default
- Domain prompt cuts term WER (word error rate) by ~40-60% in our tests
- Glossaries live in glossaries/*.txt (see core/glossary.py) so a teacher can
  switch course or language from the operator UI without editing Python.
"""

import os
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel

from .glossary import DEFAULT_GLOSSARY_ID, load_glossary


class ASRConfig:
    MODEL_SIZE = "large-v3"        # large-v3 best accuracy. medium for speed.
    DEVICE = "cuda"                # "cuda" / "cpu"
    COMPUTE_TYPE = "float16"       # "float16" on RTX 4080. "int8_float16" if VRAM tight.
    LANGUAGE = "zh"                # ISO 639-1; covers zh-TW with right prompt
    BEAM_SIZE = 5

    # Domain glossary — Whisper uses this as a soft prior for vocabulary.
    # Default = glossaries/auto_control.zh.txt. Switch at runtime with
    # SenseiASR.set_glossary(); add a course by dropping a file in glossaries/.
    _default_glossary = load_glossary(DEFAULT_GLOSSARY_ID)
    INITIAL_PROMPT = (
        _default_glossary.text if _default_glossary
        else "本逐字稿是大學課程的講課內容。"
    )

    # Local HF cache root (respects HF_HOME to avoid collision with system HF_HUB_CACHE)
    _default_cache = Path(os.environ.get("HF_HOME", r"D:\hf-cache")) / "hub"
    DOWNLOAD_ROOT = str(_default_cache) if _default_cache.is_dir() else None


class SenseiASR:
    """
    Whisper wrapper. Loads once, transcribes many times.
    """

    def _load(self, local_files_only: bool) -> WhisperModel:
        return WhisperModel(
            self.config.MODEL_SIZE,
            device=self.config.DEVICE,
            compute_type=self.config.COMPUTE_TYPE,
            download_root=self.config.DOWNLOAD_ROOT,
            local_files_only=local_files_only,
        )

    def __init__(self, config: ASRConfig = ASRConfig()):
        self.config = config
        print(f"[Sensei ASR] Loading Whisper {config.MODEL_SIZE} ({config.COMPUTE_TYPE})...")
        # Offline first. huggingface_hub's cache-miss and offline errors are
        # both OSError subclasses (LocalEntryNotFoundError -> FileNotFoundError,
        # OfflineModeIsEnabled -> ConnectionError), which is narrow enough to
        # not swallow a CUDA or compute-type failure and retry it slowly.
        try:
            self.model = self._load(local_files_only=True)
            print("[Sensei ASR] served from the local cache; no network used.")
        except OSError as e:
            print(f"[Sensei ASR] not loadable from the cache ({type(e).__name__}); "
                  f"asking the Hub. This needs a network and only happens on a "
                  f"first run or a damaged cache.", flush=True)
            self.model = self._load(local_files_only=False)
        # Runtime-switchable (operator UI): lecture language + course glossary.
        self.language: str | None = config.LANGUAGE
        self.initial_prompt: str = config.INITIAL_PROMPT
        print("[Sensei ASR] Ready.")

    def set_language(self, lang: str) -> None:
        """'zh' / 'en' / ... force a language; 'auto' lets Whisper detect it.
        Mandarin-English code-switching lectures should stay on 'zh'."""
        self.language = None if lang == "auto" else lang
        print(f"[Sensei ASR] language -> {lang}", flush=True)

    def set_glossary(self, text: str, label: str = "") -> None:
        """Replace the Whisper initial_prompt (see glossaries/README.md)."""
        self.initial_prompt = text or ""
        print(f"[Sensei ASR] glossary -> {label or 'custom'} ({len(self.initial_prompt)} chars)", flush=True)

    def transcribe(self, audio_path: str | Path) -> str:
        """File-based transcription. Returns plain text."""
        segments, info = self.model.transcribe(
            str(audio_path),
            language=self.language,
            initial_prompt=self.initial_prompt or None,
            beam_size=self.config.BEAM_SIZE,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        return "".join(seg.text for seg in segments).strip()

    def transcribe_array(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Numpy-array transcription (for live mic input).
        Audio must be mono, float32, normalized to [-1, 1].
        """
        if sample_rate != 16000:
            print(f"[Sensei ASR] Warning: expected 16kHz, got {sample_rate}Hz. "
                  "Whisper will resample but accuracy may drop.")
        segments, _ = self.model.transcribe(
            audio,
            language=self.language,
            initial_prompt=self.initial_prompt or None,
            beam_size=self.config.BEAM_SIZE,
            vad_filter=True,
        )
        return "".join(seg.text for seg in segments).strip()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m core.asr <audio_file.wav>")
        sys.exit(1)
    asr = SenseiASR()
    text = asr.transcribe(sys.argv[1])
    print(f"\n--- Transcript ---\n{text}\n")
