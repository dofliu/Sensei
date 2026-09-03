"""
Sensei · Handout export
================================
One lecture directory -> one self-contained `handout.html` the teacher can
drop on the course platform (PROPOSAL B3). Layout:

    header (course · date · card count)
    today's summary card, if the lecture produced one
    every other card in the order it was generated,
      each with its transcript folded away in <details>

Self-contained on purpose: inline CSS, no JS, no assets. The teacher mails
it, uploads it, or prints it to PDF from the browser (Ctrl+P) — that is why
there is a @media print block and why we do not add a PDF dependency.

Cards are rendered through the same `frontend.renderers` the projector uses,
so a handout looks like what the students saw on the wall.
"""

import html
import json
from datetime import datetime
from pathlib import Path

from core.session import card_files
from frontend.renderers import (
    CURRENT_THEME,
    FONT_BODY,
    FONT_MONO,
    FONT_SERIF,
    render_html,
)

# Handouts are read on paper and on phones, not projected across a room, so
# they render in the light "paper" palette regardless of the projector theme.
HANDOUT_THEME = "paper"

HANDOUT_CSS = f"""
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 0 24px 96px;
    background: #efe7d3; color: #29261b;
    font-family: {FONT_BODY};
  }}
  .wrap {{ max-width: 1100px; margin: 0 auto; }}
  header.sheet {{
    padding: 64px 0 28px; border-bottom: 2px solid #d8cdb3; margin-bottom: 40px;
  }}
  header.sheet h1 {{
    font-family: {FONT_SERIF}; font-size: 44px; line-height: 1.15;
    margin: 0 0 10px; color: #0f0d0a; font-weight: 700;
  }}
  .meta {{
    font-family: {FONT_MONO}; font-size: 13px; letter-spacing: 0.06em;
    color: #7a6a52;
  }}
  section.card {{ margin: 0 0 56px; }}
  .card-index {{
    font-family: {FONT_MONO}; font-size: 13px; letter-spacing: 0.06em;
    color: #7a6a52; margin-bottom: 10px;
  }}
  details.tx {{
    margin-top: 14px; background: #fffdf6; border: 1px solid #d8cdb3;
    border-radius: 10px; padding: 12px 18px;
  }}
  details.tx summary {{
    cursor: pointer; font-family: {FONT_MONO}; font-size: 13px;
    letter-spacing: 0.06em; color: #7a6a52;
  }}
  details.tx p {{ font-size: 17px; line-height: 1.75; color: #5c4d36; margin: 12px 0 2px; }}
  footer.sheet {{
    border-top: 1px solid #d8cdb3; padding-top: 20px; margin-top: 24px;
    font-family: {FONT_MONO}; font-size: 12px; letter-spacing: 0.06em;
    color: #7a6a52;
  }}
  @media print {{
    body {{ background: #fff; padding: 0 8mm 0; }}
    section.card {{ break-inside: avoid; margin-bottom: 28px; }}
    details.tx {{ break-inside: avoid; }}
    details.tx[open] summary {{ list-style: none; }}
    footer.sheet {{ break-before: avoid; }}
  }}
"""


def _entries(session_dir: Path) -> list[dict]:
    """Every card payload in the directory, oldest first. Filenames start with
    a %Y%m%d_%H%M%S stamp, so sorting by name is chronological."""
    out = []
    for p in card_files(session_dir):
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[Handout] skipped unreadable {p.name}: {e}", flush=True)
            continue
        if payload.get("data"):
            payload["_stem"] = p.stem
            out.append(payload)
    return out


def _card_section(payload: dict, index: str, label: str, tx_label: str) -> str:
    data = payload.get("data", {})
    body = render_html(data)
    transcript = (payload.get("transcript") or "").strip()
    tx = ""
    if transcript:
        tx = (
            f"<details class='tx'><summary>{html.escape(tx_label)}</summary>"
            f"<p>{html.escape(transcript)}</p></details>"
        )
    return (
        f"<section class='card'>"
        f"<div class='card-index'>{html.escape(index)} · {html.escape(label)}</div>"
        f"{body}{tx}</section>"
    )


def build_handout(session_dir: Path, course: str = "", date: str = "",
                  strings: dict | None = None) -> Path | None:
    """Write `<session_dir>/handout.html`. Returns the path, or None if the
    lecture has no cards yet.

    `strings` lets the caller pass the operator UI's current language; the
    zh defaults below are what a Taiwanese classroom gets.
    """
    s = {
        "title":      "課堂講義",
        "summary":    "課堂總結",
        "card":       "卡片",
        "transcript": "老師原話",
        "generated":  "由 Sensei 於 {when} 產生 · 全程在本機運算",
        "cards_n":    "{n} 張卡片",
        **(strings or {}),
    }
    entries = _entries(session_dir)
    if not entries:
        return None

    summaries = [e for e in entries if e.get("is_summary")]
    cards = [e for e in entries if not e.get("is_summary")]

    # Render in the paper palette, then restore whatever the projector is on.
    previous = CURRENT_THEME["name"]
    CURRENT_THEME["name"] = HANDOUT_THEME
    try:
        parts = [
            _card_section(e, s["summary"], e["data"].get("title", ""), s["transcript"])
            for e in summaries
        ]
        parts += [
            _card_section(e, f"{s['card']} {i}", e["data"].get("title", ""), s["transcript"])
            for i, e in enumerate(cards, start=1)
        ]
    finally:
        CURRENT_THEME["name"] = previous

    heading = course.strip() or s["title"]
    date_pretty = f"{date[:4]}-{date[4:6]}-{date[6:8]}" if len(date) >= 8 else date
    meta = " · ".join(x for x in (date_pretty, s["cards_n"].format(n=len(cards))) if x)
    when = datetime.now().strftime("%Y-%m-%d %H:%M")

    page = (
        "<!doctype html>\n<html lang='zh-TW'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(heading)} · Sensei</title>"
        "<link rel='preconnect' href='https://fonts.googleapis.com'>"
        "<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>"
        "<link rel='stylesheet' href='https://fonts.googleapis.com/css2?"
        "family=Playfair+Display:wght@400..900&family=Geist:wght@300;400;500;600;700"
        "&family=JetBrains+Mono:wght@400;500&display=swap'>"
        f"<style>{HANDOUT_CSS}</style></head><body><div class='wrap'>"
        f"<header class='sheet'><h1>{html.escape(heading)}</h1>"
        f"<div class='meta'>{html.escape(meta)}</div></header>"
        + "".join(parts)
        + f"<footer class='sheet'>{html.escape(s['generated'].format(when=when))}</footer>"
        "</div></body></html>\n"
    )

    out = session_dir / "handout.html"
    out.write_text(page, encoding="utf-8")
    print(f"[Handout] wrote {out} ({len(cards)} cards, {len(summaries)} summary)", flush=True)
    return out
