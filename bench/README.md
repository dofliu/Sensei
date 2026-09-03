# bench/

Measurement, not tests. CLAUDE.md §9 rules out a unit-test suite, CI, and the
rest of that machinery; `bench/` is the one sanctioned exception, because what
it produces is data — for tuning, and for the paper.

Nothing here runs automatically. Nothing here gates a commit.

| file | what it answers |
|---|---|
| `segmenter_probe.py` | With today's constants in `core/live_mic.py`, how does the continuous-listening segmenter behave on an empty room, a backchannel, a mid-sentence breath, a 40-second monologue, a slow pipeline, and a fan? Runs with no GPU, no mic, no Ollama. |

Planned (PROPOSAL C2): `utterances.jsonl`, a labelled set of real classroom
utterances, plus a runner that reports template hit-rate and `no_card` gate
accuracy — the numbers that decide `gemma4:e2b` vs `e4b`.

```powershell
python -m bench.segmenter_probe
```
