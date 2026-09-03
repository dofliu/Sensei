"""
Sensei · ASR glossary loader
================================
Whisper's `initial_prompt` is Sensei's main lever for engineering-jargon
accuracy. It used to be a class constant in core/asr.py, which meant changing
course or language meant editing Python. Glossaries now live as plain-text
files in `glossaries/` (see glossaries/README.md for the format) so a teacher
can add a course without touching code.

File name:  <id>.<lang>.txt   (lang: zh | en). Files starting with "_" are
            templates and are not listed.
Content:    lines starting with "#" are comments; "# title: ..." names the
            entry in the operator UI. Remaining lines are joined with spaces
            and passed verbatim to Whisper.
"""

from dataclasses import dataclass
from pathlib import Path

GLOSSARY_DIR = Path(__file__).parent.parent / "glossaries"
DEFAULT_GLOSSARY_ID = "auto_control"


@dataclass(frozen=True)
class Glossary:
    id: str
    lang: str
    title: str
    text: str
    path: Path


def _parse(path: Path) -> Glossary:
    stem_parts = path.stem.split(".")
    gid = stem_parts[0]
    lang = stem_parts[1] if len(stem_parts) > 1 else "zh"
    title = gid
    body: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            key, _, value = line.lstrip("#").strip().partition(":")
            if key.strip().lower() == "title" and value.strip():
                title = value.strip()
            continue
        body.append(line)
    return Glossary(id=gid, lang=lang, title=title, text=" ".join(body), path=path)


def list_glossaries(directory: Path = GLOSSARY_DIR) -> list[Glossary]:
    """All selectable glossaries, default first, then alphabetical by id."""
    if not directory.exists():
        return []
    items = [
        _parse(p) for p in sorted(directory.glob("*.txt"))
        if not p.name.startswith("_")
    ]
    items.sort(key=lambda g: (g.id != DEFAULT_GLOSSARY_ID, g.id))
    return items


def load_glossary(gid: str, directory: Path = GLOSSARY_DIR) -> Glossary | None:
    for g in list_glossaries(directory):
        if g.id == gid:
            return g
    return None


if __name__ == "__main__":
    for g in list_glossaries():
        print(f"{g.id:20s} [{g.lang}] {g.title}  ({len(g.text)} chars)")
