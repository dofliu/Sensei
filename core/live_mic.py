"""
Sensei · Live microphone capture
================================
Two capture modes, both server-side:

- `LiveMicCapture` — toggle recording (F8 press to start, press to stop).
  Outputs a temporary WAV path the existing pipeline consumes.
- `ContinuousListener` — always-on segmentation (PROPOSAL B1). The teacher
  presses "start listening" once and never touches the keyboard again.

Why server-side instead of browser MediaRecorder:
- Sensei's server runs on the teacher's own laptop; the mic is right there.
- One toggle button handles both start and stop without re-arming the
  browser permission dialog every time.
- The existing audio pipeline already takes a file path; we hand back
  a path and reuse the same code path as upload mode.
"""

import queue
import tempfile
import threading
import time
from collections import deque
from pathlib import Path
from threading import Lock

import numpy as np
import sounddevice as sd
import soundfile as sf


class LiveMicCapture:
    """Toggle-style microphone capture (start/stop)."""

    def __init__(self, samplerate: int = 16000, channels: int = 1):
        self.samplerate = samplerate
        self.channels = channels
        self._stream: sd.InputStream | None = None
        self._chunks: list[np.ndarray] = []
        self._lock = Lock()
        self._recording = False

    @property
    def recording(self) -> bool:
        return self._recording

    def start(self) -> None:
        """Open input stream and begin appending samples to the buffer."""
        with self._lock:
            if self._recording:
                return
            self._chunks = []
            self._recording = True
            self._stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype="float32",
                callback=self._on_audio,
            )
            self._stream.start()
        print(f"[LiveMic] Recording started · {self.samplerate} Hz mono")

    def _is_steady(self) -> bool:
        """True if recent frame energy barely varies — machinery, not a voice."""
        if len(self._rms_hist) < self._rms_hist.maxlen:
            return False
        h = np.fromiter(self._rms_hist, dtype=np.float64)
        mean = h.mean()
        return bool(mean > 0 and (h.std() / mean) < STEADY_CV)

    def _on_audio(self, indata, frames, time_info, status):
        # Audio callback runs on a sounddevice worker thread.
        # Keep this fast and lock-free — list.append is GIL-protected.
        if status:
            print(f"[LiveMic] status: {status}")
        if self._recording:
            self._chunks.append(indata.copy())

    def stop(self) -> str | None:
        """
        Stop recording and write the buffer to a temp WAV.
        Returns the WAV path, or None if no audio was captured (e.g. user
        toggled off too fast, or the input device produced no frames).
        """
        with self._lock:
            if not self._recording:
                return None
            self._recording = False
            try:
                if self._stream is not None:
                    self._stream.stop()
                    self._stream.close()
            finally:
                self._stream = None
            chunks = self._chunks
            self._chunks = []

        if not chunks:
            return None

        audio = np.concatenate(chunks, axis=0)
        duration = len(audio) / self.samplerate
        if duration < 0.3:  # too short to be useful — likely an accidental double-press
            print(f"[LiveMic] discarded {duration:.2f}s clip (too short)")
            return None

        out = Path(tempfile.gettempdir()) / f"sensei_live_{int(time.time())}.wav"
        sf.write(out, audio, self.samplerate)
        print(f"[LiveMic] Saved {duration:.1f}s -> {out}")
        return str(out)


# ────────────────────────────────────────────────────────────────────
# Continuous listening (PROPOSAL B1)
# ────────────────────────────────────────────────────────────────────
#
# Every number a teacher might want to change after their first real lecture
# is here, named, in one block. Do not scatter them into call sites.
#
# Turn-taking is segmented on frame energy against an adaptive noise floor,
# not on Silero directly: faster-whisper's Silero wrapper is an internal API
# whose shape has moved between releases, and streaming it frame-by-frame
# would tie Sensei to that shape. Silero still runs — SenseiASR.transcribe_array
# calls Whisper with vad_filter=True, so it drops non-speech *inside* each
# segment. Energy decides where an utterance ends; Silero decides what in it
# is speech.
SAMPLE_RATE          = 16000
FRAME_MS             = 32     # analysis block; 512 samples at 16 kHz
SILENCE_HANGOVER_S   = 1.2    # this much silence ends an utterance
MIN_UTTERANCE_S      = 3.0    # shorter than this is "好" / "對" / "下一頁"
MAX_UTTERANCE_S      = 25.0   # force a cut; Whisper degrades on long buffers
PRE_ROLL_S           = 0.3    # audio kept from just before speech onset
CALIBRATION_S        = 1.5    # listen to the empty room first, then set the floor
NOISE_FLOOR_ALPHA    = 0.02   # EMA rate on non-speech frames
NOISE_FLOOR_CREEP    = 0.01   # drift rate once a "sentence" is judged to be noise
STEADY_WINDOW_S      = 2.0    # how much recent RMS the steadiness test looks at
STEADY_CV            = 0.15   # coefficient of variation below this = a steady tone
SPEECH_FACTOR        = 2.5    # speech if frame RMS > noise floor x this
SPEECH_FLOOR_MIN     = 0.004  # absolute floor: a silent room is never speech
QUEUE_MAX_PENDING    = 2      # beyond this, drop the OLDEST pending utterance


class ContinuousListener:
    """Always-on mic → utterances → a single worker thread.

    `on_utterance(audio, samplerate, queued_s)` runs on that worker, one at a
    time, so ASR and the LLM never overlap. `queued_s` is how long the
    utterance sat waiting, which is the number that says whether cards are
    arriving late. If the teacher out-runs the pipeline the queue drops the
    *oldest* pending utterance: a card for something said a minute ago is
    worse than no card at all (PROPOSAL B1).

    `on_dropped(duration_s)` fires for each dropped utterance. Without it a
    drop leaves no trace anywhere - no card, no skip entry - and a lecture's
    record silently omits what the teacher actually said.
    """

    def __init__(self, on_utterance, samplerate: int = SAMPLE_RATE,
                 channels: int = 1, max_pending: int = QUEUE_MAX_PENDING,
                 on_state=None, on_dropped=None):
        self.on_utterance = on_utterance
        self.on_state = on_state          # optional: called with the stats dict
        self.on_dropped = on_dropped      # optional: called with the lost seconds
        self.samplerate = samplerate
        self.channels = channels
        self.max_pending = max_pending
        self.frame_s = FRAME_MS / 1000.0
        self.blocksize = int(samplerate * self.frame_s)

        self._stream: sd.InputStream | None = None
        self._queue: queue.Queue = queue.Queue()
        self._worker: threading.Thread | None = None
        self._lock = Lock()
        self._running = False

        self._reset_segmenter()
        self.stats = {"utterances": 0, "too_short": 0, "dropped": 0,
                      "dropped_s": 0.0, "forced": 0}

    # ── lifecycle ────────────────────────────────────────────────────
    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._reset_segmenter()
            self._running = True
            self._worker = threading.Thread(
                target=self._worker_loop, name="sensei-utterance", daemon=True
            )
            self._worker.start()
            self._stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype="float32",
                blocksize=self.blocksize,
                callback=self._on_audio,
            )
            self._stream.start()
        print(f"[LiveMic] Continuous listening started · {self.samplerate} Hz · "
              f"segment {MIN_UTTERANCE_S:.0f}-{MAX_UTTERANCE_S:.0f}s · "
              f"silence {SILENCE_HANGOVER_S}s", flush=True)

    def stop(self) -> dict:
        """Stop the stream, flush whatever is mid-utterance, drain the worker."""
        with self._lock:
            if not self._running:
                return dict(self.stats)
            self._running = False
            try:
                if self._stream is not None:
                    self._stream.stop()
                    self._stream.close()
            finally:
                self._stream = None
        self._flush(reason="stop")
        self._queue.put(None)
        if self._worker is not None:
            self._worker.join(timeout=2.0)
            self._worker = None
        print(f"[LiveMic] Continuous listening stopped · {self.stats}", flush=True)
        return dict(self.stats)

    def flush_now(self) -> bool:
        """Manual override (F8 while listening): end the current utterance now
        instead of waiting for the silence hangover. True if anything was sent."""
        return self._flush(reason="manual", min_seconds=0.5)

    # ── segmentation (runs on the sounddevice callback thread) ───────
    def _reset_segmenter(self) -> None:
        self._speaking = False
        self._voiced: list[np.ndarray] = []
        self._voiced_samples = 0
        self._silence_s = 0.0
        self._noise_floor = SPEECH_FLOOR_MIN
        # Calibration: the first CALIBRATION_S of a session is the empty room.
        # Without it the floor can never rise — it only learns from frames it
        # already called silence, so a humming projector reads as speech forever.
        self._calib_left = max(1, int(CALIBRATION_S / self.frame_s))
        self._calib_sum = 0.0
        self._calib_n = self._calib_left
        self._speech_run_s = 0.0
        self._rms_hist: deque = deque(maxlen=max(4, int(STEADY_WINDOW_S / self.frame_s)))
        self._preroll: deque = deque(maxlen=max(1, int(PRE_ROLL_S / self.frame_s)))

    def _is_steady(self) -> bool:
        """True if recent frame energy barely varies — machinery, not a voice."""
        if len(self._rms_hist) < self._rms_hist.maxlen:
            return False
        h = np.fromiter(self._rms_hist, dtype=np.float64)
        mean = h.mean()
        return bool(mean > 0 and (h.std() / mean) < STEADY_CV)

    def _on_audio(self, indata, frames, time_info, status):
        # Keep this fast: an RMS over 512 samples and a few list appends.
        if status:
            print(f"[LiveMic] status: {status}", flush=True)
        if not self._running:
            return
        block = indata.copy()
        rms = float(np.sqrt(np.mean(np.square(block), dtype=np.float64)))

        if self._calib_left > 0:
            self._calib_sum += rms
            self._calib_left -= 1
            if self._calib_left == 0:
                self._noise_floor = max(self._calib_sum / self._calib_n,
                                        SPEECH_FLOOR_MIN * 0.5)
                print(f"[LiveMic] room noise floor {self._noise_floor:.4f} "
                      f"(speech above {max(self._noise_floor * SPEECH_FACTOR, SPEECH_FLOOR_MIN):.4f})",
                      flush=True)
            self._preroll.append(block)
            return

        self._rms_hist.append(rms)
        threshold = max(self._noise_floor * SPEECH_FACTOR, SPEECH_FLOOR_MIN)
        is_speech = rms > threshold
        self._speech_run_s = self._speech_run_s + self.frame_s if is_speech else 0.0

        if not is_speech:
            self._noise_floor = (
                (1.0 - NOISE_FLOOR_ALPHA) * self._noise_floor + NOISE_FLOOR_ALPHA * rms
            )
        elif self._speech_run_s > MAX_UTTERANCE_S and self._is_steady():
            # Loud, unbroken and *flat* for longer than any real sentence: a fan
            # or an air-conditioner that started after calibration. Learn it.
            # The steadiness test is what keeps this off a genuine monologue —
            # speech level swings syllable to syllable, machinery does not.
            self._noise_floor = (
                (1.0 - NOISE_FLOOR_CREEP) * self._noise_floor + NOISE_FLOOR_CREEP * rms
            )

        if not self._speaking:
            self._preroll.append(block)
            if is_speech:
                self._speaking = True
                self._voiced = list(self._preroll)
                self._voiced_samples = sum(len(b) for b in self._voiced)
                self._preroll.clear()
                self._silence_s = 0.0
            return

        self._voiced.append(block)
        self._voiced_samples += len(block)
        self._silence_s = 0.0 if is_speech else self._silence_s + self.frame_s

        duration = self._voiced_samples / self.samplerate
        if duration >= MAX_UTTERANCE_S:
            self.stats["forced"] += 1
            # Cut here but stay in speech: the teacher is still mid-sentence.
            self._flush(reason="max-length", keep_speaking=True)
        elif self._silence_s >= SILENCE_HANGOVER_S:
            self._flush(reason="silence")

    def _flush(self, reason: str, keep_speaking: bool = False,
               min_seconds: float = MIN_UTTERANCE_S) -> bool:
        chunks, self._voiced = self._voiced, []
        samples, self._voiced_samples = self._voiced_samples, 0
        self._silence_s = 0.0
        self._speaking = keep_speaking
        if not chunks or samples == 0:
            return False
        duration = samples / self.samplerate
        if duration < min_seconds:
            self.stats["too_short"] += 1
            self._notify()
            return False
        audio = np.concatenate(chunks, axis=0)
        if audio.ndim > 1:
            audio = audio[:, 0]
        self.stats["utterances"] += 1
        print(f"[LiveMic] utterance {duration:.1f}s ({reason})", flush=True)
        self._enqueue(np.ascontiguousarray(audio, dtype=np.float32))
        return True

    # ── queue + worker ───────────────────────────────────────────────
    def _enqueue(self, audio: np.ndarray) -> None:
        while self._queue.qsize() >= self.max_pending:
            try:
                stale, _ = self._queue.get_nowait()
            except queue.Empty:
                break
            lost = len(stale) / self.samplerate
            self.stats["dropped"] += 1
            self.stats["dropped_s"] = round(self.stats["dropped_s"] + lost, 1)
            print(f"[LiveMic] queue full — dropped the oldest pending utterance "
                  f"({lost:.1f}s)", flush=True)
            if self.on_dropped is not None:
                try:
                    self.on_dropped(lost)
                except Exception as e:
                    print(f"[LiveMic] on_dropped raised: {e}", flush=True)
        self._queue.put((audio, time.monotonic()))
        self._notify()

    def _notify(self) -> None:
        if self.on_state is not None:
            try:
                self.on_state(dict(self.stats))
            except Exception as e:
                print(f"[LiveMic] on_state raised: {e}", flush=True)

    def _worker_loop(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                break
            audio, queued_at = item
            try:
                self.on_utterance(audio, self.samplerate,
                                  time.monotonic() - queued_at)
            except Exception as e:
                print(f"[LiveMic] on_utterance raised: {e}", flush=True)
            finally:
                self._notify()


if __name__ == "__main__":
    # Manual smoke test: record 3 seconds, save, print path.
    import sys
    cap = LiveMicCapture()
    print("Recording 3 seconds...")
    cap.start()
    time.sleep(3)
    path = cap.stop()
    print(f"Saved: {path}")
    sys.exit(0 if path else 1)
