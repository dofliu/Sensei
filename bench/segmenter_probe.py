"""
Sensei · Continuous-listening segmenter probe
================================
Not a test suite (CLAUDE.md §9) — a tuning tool. It runs synthetic classroom
scenarios through the REAL segmenter in `core.live_mic.ContinuousListener` and
prints what the current constants do to each one.

Use it when you come back from a lecture and something felt wrong:

    python -m bench.segmenter_probe

Then edit the constants at the top of `core/live_mic.py` and run it again.
The scenarios and what each one is protecting:

  silence only            an empty room must never produce a card
  one sentence            the basic case
  backchannel             "好" / "對" / "下一頁" must not become a card
  short pause             breathing mid-sentence must not split it
  real pause              a full stop must split it
  monologue               a teacher who never pauses still gets cards
  slow pipeline           when ASR+LLM fall behind, the OLDEST is dropped
  noisy room              a fan running at start must not read as speech
  fan starts later        a fan that starts mid-lecture must be learned

Runs with no GPU, no microphone and no Ollama — that is the point. What it
CANNOT tell you is whether Whisper transcribes your real segments well; only
a real lecture answers that.
"""

import sys
import threading
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.live_mic import (  # noqa: E402
    MAX_UTTERANCE_S, MIN_UTTERANCE_S, SILENCE_HANGOVER_S, ContinuousListener,
)

QUIET = 0.001   # an empty room
HUM   = 0.02    # projector fan / air-conditioner
VOICE = 0.30    # the lecturer

_rng = np.random.default_rng(7)
_phase = [0.0]


def feed(listener, seconds: float, amp: float, speech: bool = False) -> None:
    """Push `seconds` of synthetic audio through the segmenter's callback.

    `speech=True` adds a ~4 Hz syllable envelope. That modulation is exactly
    what separates a voice from machinery in the steadiness test, so noise
    scenarios must leave it off.
    """
    for _ in range(int(seconds / listener.frame_s)):
        a = amp
        if speech:
            _phase[0] += listener.frame_s
            a = amp * (0.25 + 0.95 * abs(np.sin(2 * np.pi * 4.0 * _phase[0])))
        block = (_rng.standard_normal((listener.blocksize, 1)) * a).astype(np.float32)
        listener._on_audio(block, listener.blocksize, None, None)


def run(name: str, script, worker_delay: float = 0.0, expect: str = "") -> None:
    got: list[float] = []

    def on_utterance(audio, sr):
        if worker_delay:
            time.sleep(worker_delay)
        got.append(len(audio) / sr)

    listener = ContinuousListener(on_utterance)
    listener._running = True          # no sound device in this probe
    listener._reset_segmenter()
    listener._worker = threading.Thread(target=listener._worker_loop, daemon=True)
    listener._worker.start()
    script(listener)
    listener._flush(reason="probe-end")
    listener._queue.put(None)
    listener._worker.join(timeout=5.0)
    listener._running = False

    st = listener.stats
    lens = " ".join(f"{d:.1f}s" for d in got) or "—"
    print(f"{name:<24} {lens:<26} sent={st['utterances']} short={st['too_short']} "
          f"dropped={st['dropped']} forced={st['forced']}")
    if expect:
        print(f"{'':<24} want: {expect}")


def main() -> None:
    print(f"silence ends an utterance at {SILENCE_HANGOVER_S}s · "
          f"keep {MIN_UTTERANCE_S}-{MAX_UTTERANCE_S}s\n")
    print(f"{'scenario':<24} {'utterances':<26} counters")
    print("-" * 86)

    run("silence only",
        lambda l: feed(l, 12, QUIET),
        expect="nothing at all")
    run("one 6s sentence",
        lambda l: (feed(l, 2, QUIET), feed(l, 6, VOICE, True), feed(l, 2, QUIET)),
        expect="exactly one utterance")
    run("1s backchannel",
        lambda l: (feed(l, 2, QUIET), feed(l, 1, VOICE, True), feed(l, 2, QUIET)),
        expect="nothing sent, short=1")
    run("0.6s pause inside",
        lambda l: (feed(l, 2, QUIET), feed(l, 4, VOICE, True), feed(l, 0.6, QUIET),
                   feed(l, 4, VOICE, True), feed(l, 2, QUIET)),
        expect="one utterance, not two")
    run("1.5s pause between",
        lambda l: (feed(l, 2, QUIET), feed(l, 5, VOICE, True), feed(l, 1.5, QUIET),
                   feed(l, 5, VOICE, True), feed(l, 2, QUIET)),
        expect="two utterances")
    run("40s monologue",
        lambda l: (feed(l, 2, QUIET), feed(l, 40, VOICE, True), feed(l, 2, QUIET)),
        expect=f"forced cut at {MAX_UTTERANCE_S:.0f}s, nothing lost")

    def flood(l):
        for _ in range(6):
            feed(l, 2, QUIET)
            feed(l, 4, VOICE, True)
            feed(l, 1.5, QUIET)
    run("pipeline 0.6s behind", flood, worker_delay=0.6,
        expect="dropped > 0 — the OLDEST, never the newest")

    run("fan running at start",
        lambda l: (feed(l, 20, HUM), feed(l, 6, VOICE, True), feed(l, 2, HUM)),
        expect="one utterance; the hum is never speech")
    run("fan starts mid-lecture",
        lambda l: (feed(l, 3, QUIET), feed(l, 6, VOICE, True), feed(l, 2, QUIET),
                   feed(l, 60, HUM), feed(l, 6, VOICE, True), feed(l, 2, HUM)),
        expect="both real utterances; the fan costs a cut or two before it is learned")


if __name__ == "__main__":
    main()
