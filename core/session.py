"""
Sensei · Lecture sessions
================================
One directory per lecture, so two courses on the same day stop bleeding into
each other's "today's summary" (PROPOSAL B3 / tech debt D8).

    history/
      20260910_auto_control_w3/     ← a session; every card of that lecture
        20260910_143012_flow_diagram.json
        20260910_143012_flow_diagram.html
        session.json                ← course name, start time
        handout.html                ← written by frontend.handout on export
      20260903_120000_swot.json     ← pre-session cards stay where they are

Deliberately simple: a single module-level holder, like CURRENT_THEME and
CURRENT_LANG. One teacher, one machine, one lecture at a time. When no
lecture has been started, `current_dir()` returns the history root, so every
existing code path keeps working untouched.
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


HISTORY_ROOT = Path(__file__).parent.parent / "history"

# A session directory is <YYYYMMDD>_<slug>; the slug keeps CJK (course names
# are Chinese) and drops only what a filesystem dislikes.
META_NAME = "session.json"

_SLUG_STRIP = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_SLUG_SPACE = re.compile(r"\s+")
SLUG_MAX_LEN = 40


@dataclass(frozen=True)
class Session:
    """An open lecture. `dir` already exists on disk."""
    course: str
    date: str          # YYYYMMDD
    started_at: str    # YYYYMMDD_HHMMSS
    dir: Path

    @property
    def label(self) -> str:
        d = self.date
        return f"{d[:4]}-{d[4:6]}-{d[6:]} · {self.course}"


# Mutable holder so handlers can flip the active session without globals dance.
ACTIVE: dict[str, Session | None] = {"session": None}


def slugify(course: str) -> str:
    """Course name → a directory-safe fragment. Keeps CJK, drops path chars."""
    s = _SLUG_STRIP.sub("", (course or "").strip())
    s = _SLUG_SPACE.sub("_", s).strip("._")
    return s[:SLUG_MAX_LEN] or "lecture"


def current() -> Session | None:
    return ACTIVE["session"]


def current_dir(root: Path | None = None) -> Path:
    """Where cards should be written / read right now.

    The active session's directory, or the history root when no lecture has
    been started. Every caller that used to glob HISTORY_DIR calls this.
    """
    s = ACTIVE["session"]
    if s is not None and s.dir.exists():
        return s.dir
    return root or HISTORY_ROOT


def start(course: str, root: Path | None = None) -> Session:
    """Open a lecture; create (or re-open) history/<date>_<slug>/.

    Re-opening the same course on the same day is intentional: the teacher
    restarts Sensei mid-lecture and the cards keep landing in one place.
    """
    base = root or HISTORY_ROOT
    now = datetime.now()
    date = now.strftime("%Y%m%d")
    d = base / f"{date}_{slugify(course)}"
    d.mkdir(parents=True, exist_ok=True)

    meta_path = d / META_NAME
    started_at = now.strftime("%Y%m%d_%H%M%S")
    if meta_path.exists():
        try:
            started_at = json.loads(meta_path.read_text(encoding="utf-8")).get(
                "started_at", started_at
            )
        except Exception:
            pass
    s = Session(course=(course or "").strip() or "lecture",
                date=date, started_at=started_at, dir=d)
    meta_path.write_text(
        json.dumps({"course": s.course, "date": s.date,
                    "started_at": s.started_at}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    ACTIVE["session"] = s
    print(f"[Session] started '{s.course}' -> {d.name}", flush=True)
    return s


def end() -> Session | None:
    """Close the lecture; new cards go back to the history root."""
    s = ACTIVE["session"]
    ACTIVE["session"] = None
    if s is not None:
        print(f"[Session] ended '{s.course}'", flush=True)
    return s


def _read_meta(d: Path) -> Session | None:
    meta = d / META_NAME
    if not meta.exists():
        return None
    try:
        m = json.loads(meta.read_text(encoding="utf-8"))
    except Exception:
        return None
    return Session(course=m.get("course", d.name),
                   date=m.get("date", d.name[:8]),
                   started_at=m.get("started_at", ""),
                   dir=d)


def list_sessions(root: Path | None = None) -> list[Session]:
    """Every session directory under history/, newest first."""
    base = root or HISTORY_ROOT
    if not base.exists():
        return []
    out = [s for d in base.iterdir() if d.is_dir()
           for s in (_read_meta(d),) if s is not None]
    return sorted(out, key=lambda s: (s.date, s.started_at), reverse=True)


def card_files(d: Path) -> list[Path]:
    """Card JSONs in a directory, oldest first, session metadata excluded.

    Every caller that used to write `dir.glob("*.json")` goes through this:
    `session.json` sorts after the %Y%m%d_-stamped card names, so a plain
    reverse-sorted glob would hand the projector the metadata file.
    """
    return sorted(p for p in d.glob("*.json") if p.name != META_NAME)


def latest_card(d: Path) -> Path | None:
    files = card_files(d)
    return files[-1] if files else None


if __name__ == "__main__":
    for s in list_sessions():
        n = len(card_files(s.dir))
        print(f"{s.dir.name:40s}  {s.label}  ({n} cards)")
