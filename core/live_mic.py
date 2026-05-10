"""
Sensei · Live microphone capture
================================
Toggle-style recording on the server side: press once to start, press
again to stop. Outputs a temporary WAV file path that the existing
pipeline can consume.

Why server-side instead of browser MediaRecorder:
- Sensei's server runs on the teacher's own laptop; the mic is right there.
- One toggle button handles both start and stop without re-arming the
  browser permission dialog every time.
- The existing audio pipeline already takes a file path; we hand back
  a path and reuse the same code path as upload mode.
"""

import tempfile
import time
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
