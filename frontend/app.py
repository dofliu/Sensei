"""
Sensei · Gradio Demo App
================================
Run:   python -m frontend.app
Open:  http://localhost:7860

Features:
- Upload / record audio, get structured visualization
- Text-input mode for fast iteration without microphone
- Live JSON view (for debugging + transparency in demo video)
- 4 template renderers (enumeration, comparison, flow, hierarchy)

This is the MVP UI. For the final demo we'll likely build a separate
fullscreen "second monitor" view in pure HTML/JS, but Gradio is perfect
for the first 3 days of iteration.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Allow running with "python -m frontend.app" from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

# Force line-buffered stdout so [Sensei LLM] runtime logs surface in real time
# under uvicorn (default block-buffering hides our prints until the buffer fills).
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

import gradio as gr
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from core.live_mic import LiveMicCapture
from core.pipeline import SenseiPipeline


# ────────────────────────────────────────────────────────────────────
# Pipeline boot — happens once at server start
# ────────────────────────────────────────────────────────────────────
print("=" * 60)
print(" Sensei · On-device AI Co-Teacher ")
print(" Loading models, please wait ~60 seconds on first run...")
print("=" * 60)
pipeline = SenseiPipeline()
live_mic = LiveMicCapture()
print("\n[OK] Sensei ready.\n")


# ────────────────────────────────────────────────────────────────────
# Renderers — one per template
# ────────────────────────────────────────────────────────────────────

THEMES = {
    "dark": {
        "container_bg": "linear-gradient(135deg,#0f172a,#1e293b)",
        "fg": "#e2e8f0",
        "fg_strong": "#f1f5f9",
        "fg_muted": "#94a3b8",
        "fg_dim": "#cbd5e1",
        "card_bg": "rgba(30,41,59,0.6)",
        "card_border": "rgba(148,163,184,0.15)",
        "table_header_bg": "rgba(148,163,184,0.08)",
        "table_border": "rgba(148,163,184,0.1)",
        "step_arrow": "#475569",
        "accents": ["#38bdf8", "#a78bfa", "#34d399", "#fb923c", "#f472b6", "#facc15"],
        "swot_s": "#34d399",  # green   — internal positive
        "swot_w": "#fb923c",  # orange  — internal negative
        "swot_o": "#38bdf8",  # blue    — external positive
        "swot_t": "#f472b6",  # magenta — external negative
        "display_bg": "#0b1220",
    },
    "light": {
        "container_bg": "linear-gradient(135deg,#f8fafc,#e2e8f0)",
        "fg": "#1e293b",
        "fg_strong": "#0f172a",
        "fg_muted": "#475569",
        "fg_dim": "#334155",
        "card_bg": "rgba(255,255,255,0.92)",
        "card_border": "rgba(15,23,42,0.12)",
        "table_header_bg": "rgba(15,23,42,0.05)",
        "table_border": "rgba(15,23,42,0.08)",
        "step_arrow": "#94a3b8",
        "accents": ["#0284c7", "#7c3aed", "#059669", "#ea580c", "#db2777", "#ca8a04"],
        "swot_s": "#059669",
        "swot_w": "#ea580c",
        "swot_o": "#0284c7",
        "swot_t": "#db2777",
        "display_bg": "#f1f5f9",
    },
    "paper": {
        # Paper editorial palette per Claude Design proposal (refined oklch low-chroma).
        "container_bg": "linear-gradient(135deg,#f6f1e6,#efe7d3)",
        "fg":           "#29261b",  # ink — body text
        "fg_strong":    "#0f0d0a",  # very dark ink — headings
        "fg_muted":     "#7a6a52",  # warm grey — meta / muted
        "fg_dim":       "#5c4d36",  # mid ink — body secondary
        "card_bg":      "#fffdf6",  # paper-on-paper
        "card_border":  "#d8cdb3",  # line — subtle paper divider
        "table_header_bg": "rgba(122,106,82,0.08)",
        "table_border":    "rgba(122,106,82,0.18)",
        "step_arrow":   "#b3a181",
        # Six accent palette, low chroma, editorial:
        "accents": ["#D97757", "#1F3A6E", "#4A7C59", "#C2741B", "#7D2E6E", "#C0392B"],
        "swot_s": "#4A7C59",  # sage green — internal positive
        "swot_w": "#D97757",  # warm orange — internal negative
        "swot_o": "#1F3A6E",  # deep blue — external positive
        "swot_t": "#C0392B",  # brick red — external negative
        "display_bg": "#f6f1e6",
    },
}

CURRENT_THEME = {"name": "dark"}  # mutable so handlers can flip it without globals dance


def _theme() -> dict:
    return THEMES[CURRENT_THEME["name"]]


def _container_style() -> str:
    t = _theme()
    return (
        f"background:{t['container_bg']};"
        f"padding:44px;border-radius:18px;color:{t['fg']};"
        f"font-family:{FONT_BODY};"
    )


def _list_themes() -> list:
    return [
        (T("theme_dark"),  "dark"),
        (T("theme_light"), "light"),
        (T("theme_paper"), "paper"),
    ]


LUCIDE_ALIASES = {
    # ───── People (top source of silent failures: LLM prefers "person" but Lucide has "user")
    "person": "user", "people": "users", "group": "users", "team": "users",
    "family": "users", "member": "user", "members": "users",
    "man": "user", "woman": "user", "child": "baby", "kid": "baby",
    "teacher": "graduation-cap", "student": "graduation-cap", "professor": "graduation-cap",
    # ───── Tools / config
    "gear": "settings", "tool": "wrench", "tools": "wrench",
    "config": "settings", "configuration": "settings", "options": "settings",
    "preferences": "settings", "fix": "wrench",
    # ───── AI / compute
    "robot": "bot", "ai": "bot", "machine": "cpu", "gpu": "cpu",
    "computer": "cpu", "pc": "cpu", "chip": "cpu",
    # ───── Charts / data
    "chart": "bar-chart-3", "graph": "line-chart",
    "stats": "bar-chart-3", "statistics": "bar-chart-3", "analytics": "bar-chart-3",
    # ───── Communication
    "chat": "message-circle", "talk": "message-circle", "discuss": "message-circle",
    "speak": "mic", "speech": "mic", "voice": "mic", "microphone": "mic",
    "email": "mail", "letter": "mail",
    # ───── Status
    "ok": "check", "success": "check-circle", "done": "check-circle",
    "warning": "alert-triangle", "danger": "alert-triangle", "caution": "alert-triangle",
    "error": "x-circle", "fail": "x-circle", "failure": "x-circle",
    "fire": "flame",
    # ───── Concepts (common in teaching)
    "idea": "lightbulb", "bulb": "lightbulb", "light": "lightbulb",
    "thinking": "brain", "thought": "brain", "mind": "brain",
    "knowledge": "book", "learn": "book-open", "study": "book-open",
    "education": "graduation-cap", "school": "graduation-cap",
    "course": "book-open", "lesson": "book-open",
    # ───── Energy / industrial (Sensei's home turf)
    "turbine": "wind", "rotor": "wind", "windmill": "wind",
    "energy": "zap", "electricity": "zap", "power": "zap", "voltage": "zap",
    "motor": "cog", "engine": "cog", "machine-part": "cog",
    "factory": "factory", "plant": "factory", "manufacturing": "factory",
    # ───── Web / world
    "world": "globe", "earth": "globe", "internet": "globe", "web": "globe",
    "online": "globe",
    # ───── Common UI
    "screen": "monitor", "desktop": "monitor", "display": "monitor",
    "house": "home", "money": "dollar-sign", "coin": "coins",
    "currency": "dollar-sign", "price": "dollar-sign",
    "date": "calendar", "schedule": "calendar", "time": "clock",
    "delete": "trash-2", "remove": "trash-2", "trash": "trash-2",
    "add": "plus", "create": "plus-circle", "new": "plus-circle",
    "edit": "pencil", "modify": "pencil", "find": "search",
    "save": "save", "load": "upload", "open": "folder-open",
    # ───── Direction / flow
    "next": "arrow-right", "prev": "arrow-left", "previous": "arrow-left",
    "up": "arrow-up", "down": "arrow-down",
    # ───── Misc that LLM commonly emits
    "lock": "lock", "secure": "shield", "security": "shield", "safe": "shield",
    "ranking": "trophy", "award": "trophy", "winner": "trophy",
    "growth": "trending-up", "increase": "trending-up", "decrease": "trending-down",
}


def _lucide_svg(name: str, color: str = "#e2e8f0") -> str:
    """
    Render a Lucide icon via CSS mask + lucide-static CDN.
    The icon shape is loaded from unpkg as an SVG; the visible colour comes
    from `color` (so accent tinting works without inlining SVG paths).

    Pipeline: lower → strip → kebab → alias-lookup → URL. Empty / missing
    names fall back to 'circle' to avoid a broken mask url. Aliases catch
    common LLM goofs (e.g. 'person' → 'user') so the demo never shows an
    empty-square icon when the LLM picks a sensible-but-wrong slug.

    Sizes scaled up for projector legibility (see CLAUDE.md §3 font rule).
    """
    icon = (name or "").strip().lower().replace(" ", "-").replace("_", "-")
    icon = LUCIDE_ALIASES.get(icon, icon)
    if not icon:
        icon = "circle"
    url = f"https://unpkg.com/lucide-static@latest/icons/{icon}.svg"
    return (
        f"<div style=\"width:56px;height:56px;border-radius:14px;"
        f"background:{color}22;display:flex;align-items:center;"
        f"justify-content:center;\">"
        f"<div style=\"width:34px;height:34px;background:{color};"
        f"-webkit-mask:url('{url}') center/contain no-repeat;"
        f"mask:url('{url}') center/contain no-repeat;\"></div>"
        f"</div>"
    )


def render_enumeration_cards(d: dict) -> str:
    """
    Paper-editorial enumeration: serif title, paper-on-paper cards with subtle shadow,
    icon + name in line, desc as Mono-flavoured caption underneath.
    """
    t = _theme()
    accents = t["accents"]
    items = d.get("items", [])
    cards = []
    for i, it in enumerate(items):
        c = accents[i % len(accents)]
        desc = (it.get("desc") or "").strip().replace("\n", " ")
        name = (it.get("name") or "").strip()
        # 防呆：LLM 偶爾把 desc 抄成 name，視覺上重複沒意義 → 直接不渲染
        if desc and desc == name:
            desc = ""
        desc_html = (
            f"<div style='font-size:20px;color:{t['fg_muted']};margin-top:12px;"
            f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
            f"line-height:1.3;font-family:{FONT_MONO};letter-spacing:0.02em;'>"
            f"&nbsp;·&nbsp;{desc}</div>"
            if desc else ""
        )
        cards.append(
            f"<div style='flex:1;min-width:280px;background:{t['card_bg']};"
            f"border:1px solid {t['card_border']};border-radius:12px;"
            f"padding:26px 24px;border-top:3px solid {c};overflow:hidden;"
            f"box-shadow:0 1px 2px rgba(15,13,10,0.05),0 2px 6px rgba(15,13,10,0.04);'>"
            f"<div style='display:flex;align-items:center;gap:18px;'>"
            f"{_lucide_svg(it.get('icon',''), c)}"
            f"<div style='font-family:{FONT_SERIF};font-size:34px;font-weight:600;"
            f"color:{t['fg_strong']};line-height:1.15;letter-spacing:-0.01em;'>{it['name']}</div>"
            f"</div>"
            f"{desc_html}"
            f"</div>"
        )
    cards_html = "".join(cards)
    subtitle_html = (
        f"<div style='font-size:22px;color:{t['fg_muted']};margin-bottom:32px;"
        f"font-style:italic;font-family:{FONT_SERIF};'>{d.get('subtitle','')}</div>"
        if d.get("subtitle") else ""
    )
    return (
        f"<div style='{_container_style()}'>"
        f"<div style='font-family:{FONT_SERIF};font-size:48px;font-weight:500;"
        f"color:{t['fg_strong']};margin-bottom:8px;line-height:1.05;letter-spacing:-0.015em;'>"
        f"{d['title']}</div>"
        f"{subtitle_html}"
        f"<div style='display:flex;gap:20px;flex-wrap:wrap;'>{cards_html}</div>"
        f"</div>"
    )


def render_comparison_table(d: dict) -> str:
    t = _theme()
    a_color = t["accents"][0]
    b_color = t["accents"][4]
    mono_label_style = (
        f"font-family:{FONT_MONO};font-size:13px;font-weight:500;"
        f"letter-spacing:0.18em;text-transform:uppercase;"
    )
    rows = "".join(
        f"<tr>"
        f"<td style='padding:20px 18px;border-bottom:1px solid {t['table_border']};"
        f"color:{t['fg_muted']};font-size:22px;font-family:{FONT_BODY};'>{r['aspect']}</td>"
        f"<td style='padding:20px 18px;border-bottom:1px solid {t['table_border']};"
        f"color:{a_color};font-size:26px;font-family:{FONT_BODY};font-weight:500;'>{r['a_value']}</td>"
        f"<td style='padding:20px 18px;border-bottom:1px solid {t['table_border']};"
        f"color:{b_color};font-size:26px;font-family:{FONT_BODY};font-weight:500;'>{r['b_value']}</td>"
        f"</tr>"
        for r in d.get("rows", [])
    )
    return (
        f"<div style='{_container_style()}'>"
        f"<div style='font-family:{FONT_SERIF};font-size:48px;font-weight:500;"
        f"color:{t['fg_strong']};margin-bottom:28px;line-height:1.05;letter-spacing:-0.015em;'>"
        f"{d['title']}</div>"
        f"<table style='width:100%;border-collapse:collapse;'>"
        f"<thead><tr style='background:{t['table_header_bg']};'>"
        f"<th style='padding:14px 18px;text-align:left;{mono_label_style}color:{t['fg_muted']};width:30%;'>"
        f"Aspect · 面向</th>"
        f"<th style='padding:14px 18px;text-align:left;{mono_label_style}color:{a_color};'>"
        f"{d['a_name']}</th>"
        f"<th style='padding:14px 18px;text-align:left;{mono_label_style}color:{b_color};'>"
        f"{d['b_name']}</th>"
        f"</tr></thead><tbody>{rows}</tbody></table></div>"
    )


def render_flow_diagram(d: dict) -> str:
    """
    Paper-editorial flow: serif title, paper-on-paper step boxes with bullet + Mono "STEP N",
    serif step name, mono description, arrow glyph between.
    """
    t = _theme()
    accents = t["accents"]
    parts = []
    steps = d.get("steps", [])
    for i, s in enumerate(steps):
        c = accents[i % len(accents)]
        desc = (s.get("desc") or "").strip().replace("\n", " ")
        name = (s.get("name") or "").strip()
        if desc and desc == name:
            desc = ""
        desc_html = (
            f"<div style='font-size:18px;color:{t['fg_muted']};margin-top:6px;"
            f"font-family:{FONT_BODY};line-height:1.35;'>{desc}</div>"
            if desc else ""
        )
        parts.append(
            f"<div style='background:{t['card_bg']};"
            f"border:1px solid {t['card_border']};border-radius:10px;padding:24px 28px;"
            f"min-width:200px;text-align:left;color:{t['fg_strong']};"
            f"box-shadow:0 1px 2px rgba(15,13,10,0.05),0 2px 6px rgba(15,13,10,0.04);'>"
            f"<div style='font-family:{FONT_MONO};font-size:13px;font-weight:500;"
            f"letter-spacing:0.18em;text-transform:uppercase;color:{t['fg_muted']};'>"
            f"<span style='color:{c};font-size:14px;'>●</span>&nbsp; STEP {i+1:02d}</div>"
            f"<div style='font-family:{FONT_SERIF};font-size:30px;font-weight:500;"
            f"margin-top:8px;line-height:1.15;letter-spacing:-0.01em;'>{s['name']}</div>"
            f"{desc_html}"
            f"</div>"
        )
        if i < len(steps) - 1:
            parts.append(
                f"<div style='font-size:30px;color:{t['step_arrow']};align-self:center;"
                f"padding:0 8px;font-family:{FONT_SERIF};'>→</div>"
            )
    return (
        f"<div style='{_container_style()}'>"
        f"<div style='font-family:{FONT_SERIF};font-size:48px;font-weight:500;"
        f"color:{t['fg_strong']};margin-bottom:32px;line-height:1.05;letter-spacing:-0.015em;'>"
        f"{d['title']}</div>"
        f"<div style='display:flex;gap:8px;align-items:stretch;flex-wrap:wrap;'>"
        f"{''.join(parts)}</div></div>"
    )


def render_hierarchy_tree(d: dict) -> str:
    t = _theme()
    accents = t["accents"]

    def render_node(node: dict, depth: int = 0) -> str:
        c = accents[depth % len(accents)]
        children = node.get("children", [])
        children_html = "".join(render_node(ch, depth + 1) for ch in children)
        # Root uses serif (heading feel); deeper levels use sans (body feel)
        if depth == 0:
            family, weight, size = FONT_SERIF, 400, 34
        elif depth == 1:
            family, weight, size = FONT_BODY, 600, 26
        else:
            family, weight, size = FONT_BODY, 500, 22
        return (
            f"<div style='margin-left:{depth*36}px;padding:9px 0;"
            f"font-family:{family};font-size:{size}px;font-weight:{weight};line-height:1.35;'>"
            f"<span style='color:{c};'>▸ </span>"
            f"<span style='color:{t['fg_strong']};'>{node['name']}</span>"
            f"</div>{children_html}"
        )

    return (
        f"<div style='{_container_style()}'>"
        f"<div style='font-family:{FONT_SERIF};font-size:48px;font-weight:500;"
        f"color:{t['fg_strong']};margin-bottom:28px;line-height:1.05;letter-spacing:-0.015em;'>"
        f"{d['title']}</div>"
        f"<div>{render_node(d['root'])}</div>"
        f"</div>"
    )


def render_swot(d: dict) -> str:
    """
    Paper-editorial SWOT 2x2: refined letter monogram + Mono label, paper card boxes.
    """
    t = _theme()
    fg_muted = t["fg_muted"]
    fg_strong = t["fg_strong"]
    card_bg = t["card_bg"]
    card_border = t["card_border"]
    quadrants = [
        ("S", "Strengths · 優勢",     d.get("strengths", []),     t["swot_s"]),
        ("W", "Weaknesses · 劣勢",    d.get("weaknesses", []),    t["swot_w"]),
        ("O", "Opportunities · 機會", d.get("opportunities", []), t["swot_o"]),
        ("T", "Threats · 威脅",       d.get("threats", []),       t["swot_t"]),
    ]
    quad_html = []
    for letter, label, items, color in quadrants:
        items_html = []
        for it in items:
            desc = (it.get("desc") or "").strip()
            desc_part = (
                f" <span style='color:{fg_muted};font-size:18px;font-family:{FONT_MONO};'>"
                f"· {desc}</span>"
                if desc else ""
            )
            items_html.append(
                f"<div style='font-size:22px;color:{fg_strong};"
                f"margin-top:9px;line-height:1.4;font-family:{FONT_BODY};'>"
                f"<span style='color:{color};font-weight:600;'>▸ </span>"
                f"{it['name']}{desc_part}</div>"
            )
        quad_html.append(
            f"<div style='background:{card_bg};border:1px solid {card_border};"
            f"border-top:3px solid {color};border-radius:12px;padding:24px 26px;"
            f"box-shadow:0 1px 2px rgba(15,13,10,0.05),0 2px 6px rgba(15,13,10,0.04);'>"
            f"<div style='display:flex;align-items:baseline;gap:12px;margin-bottom:14px;'>"
            f"<div style='font-family:{FONT_SERIF_ITALIC};font-size:44px;font-weight:500;"
            f"font-style:italic;color:{color};line-height:1;'>{letter}</div>"
            f"<div style='font-family:{FONT_MONO};font-size:13px;font-weight:500;"
            f"letter-spacing:0.18em;text-transform:uppercase;color:{fg_muted};'>"
            f"{label}</div>"
            f"</div>"
            f"{''.join(items_html)}"
            f"</div>"
        )
    subject_html = (
        f"<div style='font-size:22px;color:{fg_muted};margin-bottom:28px;"
        f"font-family:{FONT_SERIF};font-style:italic;'>{d.get('subject','')}</div>"
        if d.get("subject") else ""
    )
    return (
        f"<div style='{_container_style()}'>"
        f"<div style='font-family:{FONT_SERIF};font-size:48px;font-weight:500;"
        f"color:{fg_strong};margin-bottom:8px;line-height:1.05;letter-spacing:-0.015em;'>"
        f"{d['title']}</div>"
        f"{subject_html}"
        f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:20px;'>"
        f"{''.join(quad_html)}</div></div>"
    )


def render_pyramid(d: dict) -> str:
    """
    Paper-editorial pyramid: stacked centred slabs from narrow apex to wide base,
    each in serif name + mono caption.
    """
    t = _theme()
    accents = t["accents"]
    fg_strong = t["fg_strong"]
    fg_muted = t["fg_muted"]
    layers = d.get("layers", [])
    n = len(layers)
    if n == 0:
        return f"<div style='{_container_style()}'>(no layers)</div>"

    min_w, max_w = 36, 92
    layer_html = []
    for i, layer in enumerate(layers):
        if n == 1:
            width_pct = max_w
        else:
            width_pct = min_w + (i / (n - 1)) * (max_w - min_w)
        c = accents[i % len(accents)]
        desc = (layer.get("desc") or "").strip()
        desc_html = (
            f"<div style='font-size:16px;color:{fg_muted};margin-top:4px;"
            f"font-family:{FONT_MONO};letter-spacing:0.05em;'>{desc}</div>"
            if desc else ""
        )
        layer_html.append(
            f"<div style='width:{width_pct:.1f}%;background:{t['card_bg']};"
            f"border-left:4px solid {c};border-top:1px solid {t['card_border']};"
            f"border-right:1px solid {t['card_border']};border-bottom:1px solid {t['card_border']};"
            f"border-radius:6px;"
            f"padding:18px 28px;text-align:center;margin:6px auto;"
            f"box-shadow:0 1px 2px rgba(15,13,10,0.05),0 2px 6px rgba(15,13,10,0.04);'>"
            f"<div style='font-family:{FONT_SERIF};font-size:30px;font-weight:500;"
            f"color:{fg_strong};line-height:1.15;letter-spacing:-0.01em;'>{layer['name']}</div>"
            f"{desc_html}"
            f"</div>"
        )
    subject_html = (
        f"<div style='font-size:22px;color:{fg_muted};margin-bottom:28px;"
        f"font-family:{FONT_SERIF};font-style:italic;'>{d.get('subject','')}</div>"
        if d.get("subject") else ""
    )
    return (
        f"<div style='{_container_style()}'>"
        f"<div style='font-family:{FONT_SERIF};font-size:48px;font-weight:500;"
        f"color:{fg_strong};margin-bottom:8px;line-height:1.05;letter-spacing:-0.015em;'>"
        f"{d['title']}</div>"
        f"{subject_html}"
        f"<div>{''.join(layer_html)}</div>"
        f"</div>"
    )


RENDERERS = {
    "enumeration_cards": render_enumeration_cards,
    "comparison_table":  render_comparison_table,
    "flow_diagram":      render_flow_diagram,
    "hierarchy_tree":    render_hierarchy_tree,
    "swot":              render_swot,
    "pyramid":           render_pyramid,
}


def _render_friendly_fallback(data: dict) -> str:
    """救援也失敗時，給投影機與操作端一個有設計感的「再試一次」畫面，
    而不是把原始 JSON / Pydantic error 傾倒給觀眾看。
    完整錯誤資訊仍存在 history JSON 與 console log，研究 / debug 時可看。"""
    t = _theme()
    return (
        f"<div style='{_container_style()}'>"
        f"<div style='font-family:{FONT_SERIF_ITALIC};font-size:54px;font-weight:400;font-style:italic;"
        f"color:{t['fg_strong']};line-height:1.1;letter-spacing:-0.015em;margin-bottom:14px;'>"
        f"Sensei is thinking…</div>"
        f"<div style='font-family:{FONT_BODY};font-size:22px;color:{t['fg_muted']};"
        f"line-height:1.5;max-width:680px;'>"
        f"The model needed to retry. Please rephrase, or speak the topic again."
        f"</div>"
        f"<div style='margin-top:36px;font-family:{FONT_MONO};font-size:11px;"
        f"letter-spacing:0.18em;text-transform:uppercase;color:{t['fg_muted']};opacity:0.6;'>"
        f"Sensei · structuring engine, not oracle</div>"
        f"</div>"
    )


def render_html(data: dict) -> str:
    if not data:
        return ""
    template = data.get("template", "")
    renderer = RENDERERS.get(template)
    if renderer:
        try:
            return renderer(data)
        except Exception as e:
            print(f"[Sensei] render_html exception in {template}: {e}", flush=True)
            return _render_friendly_fallback(data)
    # Fallback for raw / unknown
    return _render_friendly_fallback(data)


# ────────────────────────────────────────────────────────────────────
# History persistence
# ────────────────────────────────────────────────────────────────────

HISTORY_DIR = Path(__file__).parent.parent / "history"
HISTORY_DIR.mkdir(exist_ok=True)

LATEST_SENTINEL = "__latest__"
TEMPLATE_HINT_AUTO = "__auto__"


# ────────────────────────────────────────────────────────────────────
# UI internationalization (operator-facing labels only).
# Card content language is a separate axis — see CURRENT_LANG / language_picker.
# ────────────────────────────────────────────────────────────────────

CURRENT_UI_LANG = {"name": "zh"}


def _ui_lang() -> str:
    return CURRENT_UI_LANG["name"]


UI_TEXTS = {
    "zh": {
        "header_md": (
            "# 🎓 Sensei\n"
            "**On-device AI co-teacher** · 把老師講的話即時整理成投影機上的視覺卡片\n"
            "不上雲端。沒有隱私風險。跑在一台筆電上。\n\n"
            "*Powered by Faster-Whisper + Gemma 4*"
        ),
        "ui_lang_label":   "介面語言",
        "theme_label":     "主題",
        "card_lang_label": "卡片語言（投影機顯示）",
        "tpl_hint_label":  "模板（按「整理成新卡片」時生效）",
        "extend_label":    "延伸來源（按「延伸上一張」時用）",
        "tab_live":        "🔴 Live 麥克風",
        "tab_audio":       "🎤 音訊輸入（檔案 / 錄音）",
        "tab_text":        "📝 文字輸入（測試用）",
        "tab_history":     "📚 歷史紀錄",
        "live_md": (
            "**課堂主要操作**：\n\n"
            "1. 按下方紅色大按鈕（或鍵盤 **F8**、設定為 F8 的簡報筆按鍵）→ 開始錄音\n"
            "2. 再按一次（或 F8）→ 停止 → 自動轉文字 → 產卡片 → 同步推到 `/display`\n\n"
            "*提示：F8 在任何 Sensei 分頁都生效；輸入文字時不會誤觸。*"
        ),
        "live_status_label": "狀態",
        "live_status_idle":  "待機中（按下方按鈕或 F8 開始）",
        "live_btn_idle":     "🎙️ 開始錄音 (F8)",
        "live_btn_recording": "⏹ 停止並生成 (F8)",
        "live_status_recording": "🔴 錄音中…再按一次（或 F8）結束並生成卡片",
        "live_status_no_audio":  "(沒有擷取到音訊；請確認麥克風裝置)",
        "live_status_done":      "✅ 已生成 — 卡片同步出現在 /display",
        "audio_in_label":     "說一段話，或上傳音檔",
        "btn_new_card":       "整理成新卡片",
        "btn_extend":         "延伸上一張",
        "text_in_label":      "貼一段老師講的話",
        "text_in_placeholder": "例：同學，控制不是只有 PID 控制，還有最佳、類神經、非線性、強健控制",
        "examples_label":     "點選範例",
        "history_md": (
            "每次生成的卡片都會自動存到 `history/` 目錄："
            "`.json` 是資料（含逐字稿），`.html` 是可直接用瀏覽器打開／截圖的卡片頁。"
        ),
        "history_dropdown_label": "選一筆紀錄（最新在最上面）",
        "history_refresh_btn":    "🔄 重新整理",
        "transcript_label":   "📝 逐字稿",
        "json_label":         "📦 結構化 JSON",
        "html_label":         "🎴 視覺化卡片",
        "hist_html_label":    "🎴 卡片重現",
        "accordion_title":    "💡 操作端輔助（不投影到 /display）",
        "summary_btn":        "📑 整理今日總結",
        "suggestions_md":     "**下一步建議** — 卡片產生後 ~3 秒會自動出現 3 個方向；點擊任一個會用該句生成下一張卡。",
        "suggest_btn_idle":   "（待生成）",
        # Theme labels
        "theme_dark":         "🌙 Dark（暗教室 / 投影機）",
        "theme_light":        "☀️ Light（亮教室 / 螢幕分享）",
        "theme_paper":        "📜 Paper（米黃紙 / 黑板派）",
        # Template hint labels
        "tpl_auto":           "🤖 自動判斷（依語意挑模板）",
        "tpl_enum":           "📇 列舉卡片（並列項目）",
        "tpl_compare":        "⚖️ 比較表（兩者差異）",
        "tpl_flow":           "➡️ 流程圖（步驟）",
        "tpl_hier":           "🌳 階層樹（分類）",
        "tpl_swot":           "🎯 SWOT 分析（優劣機威）",
        "tpl_pyramid":        "🔺 金字塔（線性層級）",
        # Extend source sentinel
        "extend_latest":      "📌 最近一張",
        # Error messages (returned by handlers when inputs are bad)
        "err_no_audio":       "請上傳音檔或錄音",
        "err_no_text":        "請輸入文字",
        "err_no_extend_text": "請輸入要新增的內容",
        "err_no_base":        "❗ 找不到要延伸的卡片（歷史是空的，或選項已失效）",
        "err_no_today":       "（今天還沒有內容可以總結）",
        "err_no_history":     "（今日歷史沒有逐字稿可彙整）",
        "err_summary_failed": "（總結生成失敗：{error}）",
        "err_no_suggestion":  "（請選擇有內容的建議）",
        "err_empty_seed":     "（建議內容為空）",
        "summary_transcript": "[今日課程總結 · 整合 {n} 段內容]",
        # Help overlay
        "help_title":         "Sensei 快捷鍵",
        "help_or":            "或",
        "help_record":        "開始 / 停止錄音（任何分頁都生效；輸入框內按不會誤觸）",
        "help_show":          "顯示這個說明",
        "help_close":         "關閉這個說明",
        "help_projector":     "投影機畫面",
        "help_fullscreen":    "F11 全螢幕",
        "help_note":          "操作介面這邊維持在筆電上、只有你會看到。",
        "help_dismiss":       "點空白處或按 Esc 關閉",
    },
    "en": {
        "header_md": (
            "# 🎓 Sensei\n"
            "**On-device AI co-teacher** · turns a lecturer's spoken words into structured visual cards in real time.\n"
            "No cloud. No privacy risk. Runs on a single laptop.\n\n"
            "*Powered by Faster-Whisper + Gemma 4*"
        ),
        "ui_lang_label":   "UI Language",
        "theme_label":     "Theme",
        "card_lang_label": "Card Language (projector display)",
        "tpl_hint_label":  "Template (applies to 'New Card')",
        "extend_label":    "Extend Source (for 'Extend' button)",
        "tab_live":        "🔴 Live Microphone",
        "tab_audio":       "🎤 Audio Input (file / record)",
        "tab_text":        "📝 Text Input (testing)",
        "tab_history":     "📚 History",
        "live_md": (
            "**Primary classroom flow**:\n\n"
            "1. Click the red button below (or **F8**, or a presenter pen key mapped to F8) → start recording\n"
            "2. Click again (or F8) → stop → auto-transcribe → generate card → push to `/display`\n\n"
            "*Tip: F8 works from any tab; it never fires while typing in a text field.*"
        ),
        "live_status_label": "Status",
        "live_status_idle":  "Idle (click the button below or press F8 to start)",
        "live_btn_idle":     "🎙️ Start Recording (F8)",
        "live_btn_recording": "⏹ Stop & Generate (F8)",
        "live_status_recording": "🔴 Recording… press again (or F8) to stop and generate the card",
        "live_status_no_audio":  "(No audio captured; please check the microphone device)",
        "live_status_done":      "✅ Card generated — synced to /display",
        "audio_in_label":     "Speak, or upload an audio file",
        "btn_new_card":       "New Card",
        "btn_extend":         "Extend Last",
        "text_in_label":      "Paste a snippet of the lecture",
        "text_in_placeholder": "e.g. Students, control isn't only PID — there's also optimal, neural, nonlinear, and robust control",
        "examples_label":     "Click an example",
        "history_md": (
            "Every generated card is saved to `history/`: `.json` (data + transcript) and "
            "`.html` (a standalone page you can open in a browser or screenshot)."
        ),
        "history_dropdown_label": "Pick a record (newest first)",
        "history_refresh_btn":    "🔄 Refresh",
        "transcript_label":   "📝 Transcript",
        "json_label":         "📦 Structured JSON",
        "html_label":         "🎴 Visual Card",
        "hist_html_label":    "🎴 Card replay",
        "accordion_title":    "💡 Operator Tools (not projected to /display)",
        "summary_btn":        "📑 Today's Summary",
        "suggestions_md":     "**Next-step suggestions** — three directions appear ~3 s after each card. Click one to seed the next card.",
        "suggest_btn_idle":   "(generating…)",
        # Theme labels
        "theme_dark":         "🌙 Dark (dim classroom / projector)",
        "theme_light":        "☀️ Light (bright classroom / screen share)",
        "theme_paper":        "📜 Paper (editorial / chalkboard feel)",
        # Template hint labels
        "tpl_auto":           "🤖 Auto-detect (let the model pick)",
        "tpl_enum":           "📇 Enumeration cards (parallel items)",
        "tpl_compare":        "⚖️ Comparison table (A vs B)",
        "tpl_flow":           "➡️ Flow diagram (steps)",
        "tpl_hier":           "🌳 Hierarchy tree (sub-classes)",
        "tpl_swot":           "🎯 SWOT analysis",
        "tpl_pyramid":        "🔺 Pyramid (linear layers)",
        # Extend source sentinel
        "extend_latest":      "📌 Most recent card",
        # Error messages
        "err_no_audio":       "Please upload audio or record first",
        "err_no_text":        "Please type some text",
        "err_no_extend_text": "Please type the content to add",
        "err_no_base":        "❗ No card to extend (history is empty, or selection is stale)",
        "err_no_today":       "(No content to summarize today yet)",
        "err_no_history":     "(Today's history has no transcripts to compile)",
        "err_summary_failed": "(Summary failed: {error})",
        "err_no_suggestion":  "(Please pick a suggestion that has content)",
        "err_empty_seed":     "(Suggestion content is empty)",
        "summary_transcript": "[Today's session summary · {n} segments combined]",
        # Help overlay
        "help_title":         "Sensei Hotkeys",
        "help_or":            "or",
        "help_record":        "Start / stop recording (works from any tab; never fires while typing)",
        "help_show":          "Show this help",
        "help_close":         "Close this help",
        "help_projector":     "Projector view",
        "help_fullscreen":    "F11 fullscreen",
        "help_note":          "The operator console stays on your laptop — students never see it.",
        "help_dismiss":       "Click outside or press Esc to dismiss",
    },
}


def T(key: str) -> str:
    """Look up an operator-UI string in the current language."""
    return UI_TEXTS[_ui_lang()].get(key, UI_TEXTS["zh"].get(key, key))


def _list_ui_languages() -> list:
    return [("中文", "zh"), ("English", "en")]

CURRENT_LANG = {"name": "zh"}  # mutable container so handlers flip without globals dance


def _lang() -> str:
    return CURRENT_LANG["name"]


def _list_languages() -> list:
    return [
        ("中文（原始）",                  "zh"),
        ("English",                       "en"),
        ("日本語（Japanese）",            "ja"),
        ("한국어（Korean）",              "ko"),
        ("Tiếng Việt（Vietnamese）",      "vi"),
        ("Bahasa Indonesia（Indonesian）", "id"),
        ("Español（Spanish）",            "es"),
        ("Français（French）",            "fr"),
    ]


def _persist_translation(json_path: Path, target_lang: str, translated: dict) -> None:
    """寫回歷史檔，把指定語言的版本加進去（欄位名 data_{lang}），避免下次重新呼叫 LLM。"""
    if not json_path.exists():
        return
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        payload[f"data_{target_lang}"] = translated
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"[Sensei] failed to persist translation: {e}", flush=True)


def _translate_and_persist(data: dict, json_path: Path | None) -> dict:
    """若 lang!=zh，呼叫 Gemma 4 翻譯並寫回歷史檔；否則原樣回傳。"""
    target = _lang()
    if target == "zh":
        return data
    if not data or data.get("template") in (None, "raw"):
        return data
    try:
        translated = pipeline.llm.translate(data, target_lang=target)
    except Exception as e:
        print(f"[Sensei] translation failed: {e}", flush=True)
        return data
    if json_path is not None:
        _persist_translation(json_path, target, translated)
    return translated


def _list_template_hints() -> list:
    """模板提示下拉選項。要再加新模板就 append 在這裡。"""
    return [
        (T("tpl_auto"),    TEMPLATE_HINT_AUTO),
        (T("tpl_enum"),    "enumeration_cards"),
        (T("tpl_compare"), "comparison_table"),
        (T("tpl_flow"),    "flow_diagram"),
        (T("tpl_hier"),    "hierarchy_tree"),
        (T("tpl_swot"),    "swot"),
        (T("tpl_pyramid"), "pyramid"),
    ]


def _history_label(p: Path) -> str:
    """產生 dropdown 顯示用的標籤：時間 · 模板 · ↳延伸標記 · 標題。"""
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return p.stem
    ts = payload.get("timestamp", p.stem)
    data = payload.get("data", {}) or {}
    template = (data.get("template") or "raw").replace("_", " ")
    title = data.get("title", "")
    extended = "↳ " if payload.get("extends_from") else ""
    if len(ts) >= 13:
        ts_pretty = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}"
    else:
        ts_pretty = ts
    title_short = (title[:18] + "…") if len(title) > 18 else title
    return f"{ts_pretty} · {template} · {extended}{title_short}".strip(" ·")


def _list_history_choices() -> list:
    """最新在前；choices = [(label, value)]，value 是 JSON 檔絕對路徑。"""
    entries = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
    return [(_history_label(p), str(p)) for p in entries]


def _list_extend_choices() -> list:
    """延伸來源下拉：「最近一張」固定第一筆，後面接所有歷史紀錄。"""
    return [(T("extend_latest"), LATEST_SENTINEL)] + _list_history_choices()


def _resolve_base(source_value: str):
    """
    依照下拉選項解析出要延伸的基底卡片。
    回傳 (json 檔路徑, data dict)；若找不到回傳 None。
    """
    if source_value == LATEST_SENTINEL:
        entries = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
        if not entries:
            return None
        p = entries[0]
    elif source_value:
        p = Path(source_value)
        if not p.exists():
            return None
    else:
        return None
    payload = json.loads(p.read_text(encoding="utf-8"))
    data = payload.get("data")
    if not data:
        return None
    return p, data


def _save_to_history(
    data: dict,
    transcript: str,
    extends_from: str | None = None,
    is_summary: bool = False,
) -> Path | None:
    """把一次生成結果同時存成 JSON（資料）與 HTML（可開啟／截圖的卡片）。
    回傳 JSON 檔絕對路徑，給 caller 用來後續寫回翻譯快取。"""
    if not data or "template" not in data:
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    template = data.get("template", "raw")
    base = f"{ts}_{template}{'_summary' if is_summary else ''}"
    payload = {"timestamp": ts, "transcript": transcript, "data": data}
    if extends_from:
        payload["extends_from"] = extends_from
    if is_summary:
        payload["is_summary"] = True
    json_path = HISTORY_DIR / f"{base}.json"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    title = data.get("title", base)
    standalone = (
        "<!doctype html><meta charset='utf-8'>"
        f"<title>{title}</title>"
        "<body style=\"margin:0;padding:24px;background:#0b1220;"
        "font-family:'Noto Sans TC',-apple-system,sans-serif;\">"
        f"{render_html(data)}"
        "</body>"
    )
    (HISTORY_DIR / f"{base}.html").write_text(standalone, encoding="utf-8")
    return json_path


def load_history_entry(json_path: str):
    if not json_path:
        return "", "{}", ""
    p = Path(json_path)
    if not p.exists():
        return "(已刪除)", "{}", ""
    payload = json.loads(p.read_text(encoding="utf-8"))
    transcript = payload.get("transcript", "")
    data = payload.get("data", {})
    return transcript, json.dumps(data, ensure_ascii=False, indent=2), render_html(data)


def refresh_dropdowns():
    """重新整理兩個下拉：延伸來源（重設為最近一張）+ 歷史紀錄。"""
    return (
        gr.Dropdown(choices=_list_extend_choices(), value=LATEST_SENTINEL),
        gr.Dropdown(choices=_list_history_choices()),
    )


def _resolve_payload_for_lang(payload: dict, json_path: Path | None) -> dict:
    """讀 history payload，依當前語言回傳要渲染的 data；
    需要非中文且未快取時才呼叫 LLM 翻譯並寫回。"""
    target = _lang()
    if target == "zh":
        return payload.get("data", {})
    field = f"data_{target}"
    cached = payload.get(field)
    if cached:
        return cached
    try:
        translated = pipeline.llm.translate(payload.get("data", {}), target_lang=target)
    except Exception as e:
        print(f"[Sensei] translation failed: {e}", flush=True)
        return payload.get("data", {})
    if json_path is not None:
        _persist_translation(json_path, target, translated)
    return translated


def handle_theme_change(theme_name: str):
    """切主題：套用後立刻重新渲染最新一張卡片到操作畫面；/display 下次輪詢時自動換色。"""
    if theme_name in THEMES:
        CURRENT_THEME["name"] = theme_name
    entries = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
    if not entries:
        return ""
    try:
        payload = json.loads(entries[0].read_text(encoding="utf-8"))
    except Exception:
        return ""
    data = _resolve_payload_for_lang(payload, entries[0])
    return render_html(data)


def update_suggestions_after_gen():
    """生卡之後跑：呼叫 LLM 出 3 個下一步建議，更新 3 顆按鈕的 label 與可見性。
    用 .then() 鏈在 generate handler 之後，所以**不阻塞**卡片渲染 — 卡片先出現、建議再淡入。"""
    print("[Sensei] update_suggestions_after_gen fired", flush=True)
    entries = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
    if not entries:
        print("[Sensei]   no history entries", flush=True)
        return tuple(gr.update(visible=False) for _ in range(3))
    try:
        payload = json.loads(entries[0].read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[Sensei]   read history failed: {e}", flush=True)
        return tuple(gr.update(visible=False) for _ in range(3))
    if payload.get("is_summary"):
        print("[Sensei]   latest is summary; hiding suggestions", flush=True)
        return tuple(gr.update(visible=False) for _ in range(3))
    data = payload.get("data") or {}
    if data.get("template") in (None, "raw"):
        print(f"[Sensei]   latest template is {data.get('template')}; hiding", flush=True)
        return tuple(gr.update(visible=False) for _ in range(3))
    try:
        suggestions = pipeline.llm.suggest_next(data)
    except Exception as e:
        print(f"[Sensei]   suggest_next exception: {e}", flush=True)
        return tuple(gr.update(visible=False) for _ in range(3))

    print(f"[Sensei]   got {len(suggestions)} suggestions: {suggestions}", flush=True)
    updates = []
    for i in range(3):
        if i < len(suggestions) and suggestions[i]:
            updates.append(gr.update(value=f"💡 {suggestions[i]}", visible=True))
        else:
            updates.append(gr.update(visible=False))
    return tuple(updates)


def handle_suggestion_click(btn_value: str):
    """點擊任一建議按鈕：用按鈕文字當作種子，走 handle_text 路徑生成新卡片。"""
    print(f"[Sensei] suggestion clicked: {btn_value!r}", flush=True)
    if not btn_value:
        return T("err_no_suggestion"), "{}", ""
    seed = btn_value.lstrip("💡 ").strip()
    if not seed:
        return T("err_empty_seed"), "{}", ""
    return handle_text(seed, TEMPLATE_HINT_AUTO)


def handle_suggestion_chain(btn_value: str):
    """合併處理：點建議 → 生新卡 → 更新下拉 → 更新建議按鈕，**一次回傳全部**。
    避開 .then() 鏈在按鈕反覆替換 value 時可能的時序問題。"""
    transcript_v, json_v, html_v = handle_suggestion_click(btn_value)
    extend_v, history_v = refresh_dropdowns()
    sugg_updates = update_suggestions_after_gen()
    return (
        transcript_v, json_v, html_v,
        extend_v, history_v,
        sugg_updates[0], sugg_updates[1], sugg_updates[2],
    )


def handle_summarize_today():
    """整理今日所有歷史紀錄成一張 enumeration_cards 總結卡。"""
    today = datetime.now().strftime("%Y%m%d")
    files = sorted(HISTORY_DIR.glob(f"{today}_*.json"))
    if not files:
        return T("err_no_today"), "{}", ""

    transcripts: list[str] = []
    for fp in files:
        try:
            payload = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if payload.get("is_summary"):
            continue
        tx = (payload.get("transcript") or "").strip()
        if tx:
            transcripts.append(tx)

    if not transcripts:
        return T("err_no_history"), "{}", ""

    date_pretty = f"{today[:4]}-{today[4:6]}-{today[6:]}"
    result = pipeline.llm.summarize_session(transcripts, date_str=date_pretty)
    if result.get("template") == "raw":
        return T("err_summary_failed").format(error=result.get("_error", "?")), "{}", ""

    summary_transcript = T("summary_transcript").format(n=len(transcripts))
    saved = _save_to_history(result, summary_transcript, is_summary=True)
    display_data = _translate_and_persist(result, saved)
    return summary_transcript, json.dumps(result, ensure_ascii=False, indent=2), render_html(display_data)


def handle_ui_language_change(ui_lang_value: str):
    """切操作介面語言：更新所有 UI 元件 label / value / choices。
    回傳值的順序必須跟 wiring 的 outputs 列表一致。"""
    if ui_lang_value in ("zh", "en"):
        CURRENT_UI_LANG["name"] = ui_lang_value
    # Build dropdown choices in new language; preserve current selection where possible
    overlay_value = build_hotkey_overlay_html().replace("__SENSEI_CSS__", SENSEI_CSS)
    return (
        # Markdown blocks
        gr.update(value=T("header_md")),                          # header_md
        gr.update(value=T("live_md")),                            # live_md
        gr.update(value=T("history_md")),                         # history_md
        gr.update(value=T("suggestions_md")),                     # suggestions_md
        # Top-row dropdowns: label updates + new translated choices (value preserved by key)
        gr.update(label=T("ui_lang_label")),                      # ui_language_picker
        gr.update(label=T("theme_label"), choices=_list_themes()),               # theme_picker
        gr.update(label=T("card_lang_label")),                    # language_picker
        gr.update(label=T("tpl_hint_label"), choices=_list_template_hints()),    # template_hint
        gr.update(label=T("extend_label"),   choices=_list_extend_choices()),    # extend_source
        # Tabs (label = tab title)
        gr.update(label=T("tab_live")),                           # tab_live
        gr.update(label=T("tab_audio")),                          # tab_audio
        gr.update(label=T("tab_text")),                           # tab_text
        gr.update(label=T("tab_history")),                        # tab_history
        # Live tab specifics
        gr.update(label=T("live_status_label"),
                  value=T("live_status_recording") if live_mic.recording else T("live_status_idle")),
        gr.update(value=T("live_btn_recording") if live_mic.recording else T("live_btn_idle")),
        # Audio tab
        gr.update(label=T("audio_in_label")),
        gr.update(value=T("btn_new_card")),
        gr.update(value=T("btn_extend")),
        # Text tab
        gr.update(label=T("text_in_label"), placeholder=T("text_in_placeholder")),
        gr.update(value=T("btn_new_card")),
        gr.update(value=T("btn_extend")),
        # History tab
        gr.update(label=T("history_dropdown_label")),
        gr.update(value=T("history_refresh_btn")),
        gr.update(label=T("transcript_label")),
        gr.update(label=T("json_label")),
        gr.update(label=T("hist_html_label")),
        # Output row
        gr.update(label=T("transcript_label")),
        gr.update(label=T("json_label")),
        gr.update(label=T("html_label")),
        # Accordion + summary + overlay HTML
        gr.update(label=T("accordion_title")),
        gr.update(value=T("summary_btn")),
        gr.update(value=overlay_value),                           # overlay_html_block
    )


def handle_language_change(lang_value: str):
    """切語言：更新全域狀態，重新渲染最新卡片；
    若切到非中文且該語言版本未快取，呼叫 LLM 翻譯並寫回歷史檔。"""
    valid_codes = {"zh"} | set(SenseiLLM_target_codes())
    if lang_value in valid_codes:
        CURRENT_LANG["name"] = lang_value
    entries = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
    if not entries:
        return ""
    try:
        payload = json.loads(entries[0].read_text(encoding="utf-8"))
    except Exception:
        return ""
    data = _resolve_payload_for_lang(payload, entries[0])
    return render_html(data)


def SenseiLLM_target_codes() -> set:
    """晚綁定，避免 import 期 circular issues。"""
    from core.llm import SenseiLLM
    return set(SenseiLLM.TRANSLATION_TARGETS.keys())


# ────────────────────────────────────────────────────────────────────
# Gradio handlers
# ────────────────────────────────────────────────────────────────────

def _resolve_hint(hint_value: str) -> str | None:
    """把 dropdown 的 sentinel 換成 None（自動判斷）或模板名。"""
    return None if hint_value == TEMPLATE_HINT_AUTO else hint_value


def handle_audio(audio_path, hint_value):
    if not audio_path:
        return T("err_no_audio"), "{}", ""
    result = pipeline.process_audio(audio_path, template_hint=_resolve_hint(hint_value))
    transcript = result.pop("_transcript", "")
    saved = _save_to_history(result, transcript)
    display_data = _translate_and_persist(result, saved)
    return transcript, json.dumps(result, ensure_ascii=False, indent=2), render_html(display_data)


def handle_text(text, hint_value):
    if not (text or "").strip():
        return T("err_no_text"), "{}", ""
    result = pipeline.process_text(text, template_hint=_resolve_hint(hint_value))
    transcript = result.pop("_transcript", "")
    saved = _save_to_history(result, transcript)
    display_data = _translate_and_persist(result, saved)
    return transcript, json.dumps(result, ensure_ascii=False, indent=2), render_html(display_data)


# ────────────────────────────────────────────────────────────────────
# Live mic toggle handler
# ────────────────────────────────────────────────────────────────────

def handle_live_toggle(hint_value):
    """
    第一次按：開始錄音。第二次按：停止 → ASR → LLM → 渲染。
    回傳 5 個元素：button label / status text / transcript / json / html
    """
    if not live_mic.recording:
        live_mic.start()
        return (
            gr.update(value=T("live_btn_recording"), variant="stop"),
            T("live_status_recording"),
            gr.update(),
            gr.update(),
            gr.update(),
        )
    wav_path = live_mic.stop()
    if not wav_path:
        return (
            gr.update(value=T("live_btn_idle"), variant="primary"),
            T("live_status_no_audio"),
            gr.update(),
            gr.update(),
            gr.update(),
        )
    result = pipeline.process_audio(wav_path, template_hint=_resolve_hint(hint_value))
    transcript = result.pop("_transcript", "")
    saved = _save_to_history(result, transcript)
    display_data = _translate_and_persist(result, saved)
    return (
        gr.update(value=T("live_btn_idle"), variant="primary"),
        T("live_status_done"),
        transcript,
        json.dumps(result, ensure_ascii=False, indent=2),
        render_html(display_data),
    )


def handle_audio_extend(audio_path, source_value):
    if not audio_path:
        return T("err_no_audio"), "{}", ""
    base = _resolve_base(source_value)
    if base is None:
        return T("err_no_base"), "{}", ""
    base_path, base_data = base
    result = pipeline.extend_with_audio(base_data, audio_path)
    transcript = result.pop("_transcript", "")
    saved = _save_to_history(result, transcript, extends_from=base_path.stem)
    display_data = _translate_and_persist(result, saved)
    return transcript, json.dumps(result, ensure_ascii=False, indent=2), render_html(display_data)


def handle_text_extend(text, source_value):
    if not (text or "").strip():
        return T("err_no_extend_text"), "{}", ""
    base = _resolve_base(source_value)
    if base is None:
        return T("err_no_base"), "{}", ""
    base_path, base_data = base
    result = pipeline.extend_with_text(base_data, text)
    transcript = result.pop("_transcript", "")
    saved = _save_to_history(result, transcript, extends_from=base_path.stem)
    display_data = _translate_and_persist(result, saved)
    return transcript, json.dumps(result, ensure_ascii=False, indent=2), render_html(display_data)


# ────────────────────────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────────────────────────

EXAMPLES = [
    "同學，控制不是只有 PID 控制，還有最佳、類神經、非線性、強健控制",
    "我們來比較一下單迴路與雙迴路控制：單迴路結構簡單成本低，雙迴路抗擾能力較佳但需要兩個感測器",
    "風機監控系統的流程是這樣，先量測振動，再做特徵抽取，然後做診斷，最後報警",
    "機器學習可以分為監督式、非監督式、強化學習三大類，監督式裡又分為分類與迴歸",
]


# Primary serif uses Playfair Display (multi-weight 400-900); Instrument Serif kept
# as italic-flavoured accent (single weight 400, beautiful for italic moments only).
FONT_SERIF        = "'Playfair Display', 'Noto Serif TC', Georgia, serif"
FONT_SERIF_ITALIC = "'Instrument Serif', 'Playfair Display', 'Noto Serif TC', Georgia, serif"
FONT_BODY         = "'Geist', 'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif"
FONT_MONO         = "'JetBrains Mono', Menlo, Consolas, monospace"


# ────────────────────────────────────────────────────────────────────
# Gradio theme + CSS — 把操作介面從 SaaS 灰調成 paper editorial
# ────────────────────────────────────────────────────────────────────

SENSEI_THEME = gr.themes.Soft(
    # Primary (主互動色) — 暖橘，跟 paper 主題的 accents[0] 對齊
    primary_hue=gr.themes.Color(
        c50  = "#fdf6e3",
        c100 = "#fbe7c4",
        c200 = "#f5cba0",
        c300 = "#ed9c6e",
        c400 = "#e2854e",
        c500 = "#D97757",  # ← brand orange
        c600 = "#c25d3b",
        c700 = "#a44830",
        c800 = "#7d3424",
        c900 = "#522518",
        c950 = "#2d130c",
    ),
    secondary_hue="amber",
    # Neutral (背景 / 邊框 / 文字) — warm stone with paper undertone
    neutral_hue=gr.themes.Color(
        c50  = "#fffdf6",  # paper card
        c100 = "#f6f1e6",  # paper bg
        c200 = "#efe7d3",
        c300 = "#d8cdb3",  # line
        c400 = "#b3a181",
        c500 = "#7a6a52",  # mute
        c600 = "#5c4d36",
        c700 = "#3a322a",
        c800 = "#29261b",  # ink
        c900 = "#1c1a13",
        c950 = "#0f0d0a",
    ),
    font=[gr.themes.GoogleFont("Geist"), "Noto Sans TC", "ui-sans-serif", "system-ui"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "Menlo"],
    radius_size=gr.themes.sizes.radius_md,
    text_size=gr.themes.sizes.text_md,
)

SENSEI_CSS = """
/* Make the whole canvas paper, not the default off-white */
body, .gradio-container, .gradio-container > div {
    background: #f6f1e6 !important;
}

/* Markdown headings — serif editorial */
.gradio-container .prose h1,
.gradio-container .prose h2,
.gradio-container .prose h3,
.gradio-container .prose h4,
.gradio-container .markdown h1,
.gradio-container .markdown h2,
.gradio-container .markdown h3,
.gradio-container .markdown h4 {
    font-family: 'Playfair Display', 'Noto Serif TC', Georgia, serif !important;
    color: #29261b !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em !important;
    margin-top: 0.4em !important;
    margin-bottom: 0.3em !important;
}
.gradio-container .prose h1 { font-size: 38px !important; }
.gradio-container .prose h2 { font-size: 28px !important; }
.gradio-container .prose h3 { font-size: 22px !important; }

/* Form labels — uppercase Mono, like editorial captions */
.gradio-container label > span,
.gradio-container .label-wrap > span,
.gradio-container .block-label,
.gradio-container span[data-testid="block-label"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: #7a6a52 !important;
    font-weight: 500 !important;
}

/* Hide Gradio attribution footer / API button */
footer { display: none !important; }
.footer { display: none !important; }
button.show-api, .show-api { display: none !important; }
.gradio-container > .footer { display: none !important; }

/* Code block — paper card */
.gradio-container .code-wrap,
.gradio-container .codemirror-wrapper {
    background: #fffdf6 !important;
    border: 1px solid #d8cdb3 !important;
    border-radius: 10px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Tab nav — clean, accent underline */
.gradio-container .tab-nav button {
    font-family: 'Geist', sans-serif !important;
    color: #7a6a52 !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
    font-weight: 500 !important;
    padding: 10px 16px !important;
}
.gradio-container .tab-nav button.selected {
    color: #29261b !important;
    border-bottom-color: #D97757 !important;
    background: transparent !important;
}

/* Inputs and dropdowns — paper card with warm border */
.gradio-container input[type="text"],
.gradio-container input[type="number"],
.gradio-container textarea,
.gradio-container select,
.gradio-container .wrap-inner,
.gradio-container .container > .wrap {
    background: #fffdf6 !important;
    border: 1px solid #d8cdb3 !important;
    color: #29261b !important;
    border-radius: 8px !important;
    font-family: 'Geist', sans-serif !important;
}
.gradio-container input[type="text"]:focus,
.gradio-container textarea:focus {
    border-color: #D97757 !important;
    box-shadow: 0 0 0 3px rgba(217, 119, 87, 0.18) !important;
    outline: none !important;
}

/* Container blocks (gr.Tab content, gr.Row, gr.Column) — pure paper */
.gradio-container .block,
.gradio-container .panel,
.gradio-container .form,
.gradio-container .gap {
    background: transparent !important;
}

/* Card-like wrapper around inputs / outputs */
.gradio-container .gradio-container > div > div,
.gradio-container .form > div {
    background: transparent !important;
}

/* Accordion (the "操作端輔助" panel) */
.gradio-container .label-wrap[data-testid="accordion-label"],
.gradio-container details summary {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: #7a6a52 !important;
}

/* HTML output (the rendered card) — let the card itself draw, no outer chrome */
.gradio-container .html-container,
.gradio-container [data-testid="html"] {
    background: transparent !important;
    border: none !important;
}
"""



def build_hotkey_overlay_html() -> str:
    """產生 hotkey help overlay 的 HTML。依當前 UI 語言切換內容。"""
    return f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<!-- Sensei CSS injected via HTML so it persists regardless of Gradio launch path -->
<style id="sensei-operator-css">__SENSEI_CSS__</style>
<div id="sensei-help-overlay" style="
    display:none;position:fixed;inset:0;z-index:9999;
    background:rgba(0,0,0,0.6);
    align-items:center;justify-content:center;
    font-family:'Geist','Noto Sans TC',-apple-system,sans-serif;">
  <div style="
      background:#0f172a;color:#e2e8f0;
      border:1px solid rgba(148,163,184,0.2);
      border-radius:14px;padding:32px 36px;
      max-width:580px;box-shadow:0 12px 40px rgba(0,0,0,0.5);">
    <div style="font-size:24px;font-weight:700;margin-bottom:18px;">
      ⌨️ {T("help_title")}
    </div>
    <table style="width:100%;border-collapse:collapse;font-size:16px;">
      <tr><td style="padding:8px 0;width:180px;">
        <code style="background:#1e293b;padding:3px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace;">F8</code>
        &nbsp;{T("help_or")}&nbsp;
        <code style="background:#1e293b;padding:3px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace;">Ctrl + Space</code>
      </td><td>{T("help_record")}</td></tr>
      <tr><td style="padding:8px 0;">
        <code style="background:#1e293b;padding:3px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace;">?</code>
      </td><td>{T("help_show")}</td></tr>
      <tr><td style="padding:8px 0;">
        <code style="background:#1e293b;padding:3px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace;">Esc</code>
      </td><td>{T("help_close")}</td></tr>
    </table>
    <div style="margin-top:22px;padding-top:18px;border-top:1px solid rgba(148,163,184,0.15);font-size:13px;color:#94a3b8;line-height:1.6;">
      {T("help_projector")}：<code style="background:#1e293b;padding:2px 6px;border-radius:4px;font-family:'JetBrains Mono',monospace;">http://localhost:7860/display</code>（{T("help_fullscreen")}）<br>
      {T("help_note")}
    </div>
    <div style="text-align:right;margin-top:18px;font-size:12px;color:#64748b;">
      {T("help_dismiss")}
    </div>
  </div>
</div>
"""


# Initial value computed at module import time; will be re-computed in handler when UI lang switches
HOTKEY_OVERLAY_HTML = build_hotkey_overlay_html()


HOTKEY_INSTALL_JS = """
if (!window.__senseiHotkeyBound) {
    window.__senseiHotkeyBound = true;
    console.log('[Sensei] hotkey listener installed (F8 / Ctrl+Space / ?)');

    function showHelp() {
        const o = document.getElementById('sensei-help-overlay');
        if (o) o.style.display = 'flex';
    }
    function hideHelp() {
        const o = document.getElementById('sensei-help-overlay');
        if (o) o.style.display = 'none';
    }

    document.addEventListener('keydown', function(e) {
        const t = (e.target.tagName || '').toLowerCase();
        const inField = (t === 'input' || t === 'textarea');

        // F8 / Ctrl+Space → toggle recording
        const isF8 = (e.key === 'F8' || e.code === 'F8');
        const isCtrlSpace = e.ctrlKey && e.code === 'Space';
        if ((isF8 || isCtrlSpace) && !inField) {
            e.preventDefault();
            e.stopPropagation();
            var btn = document.querySelector('#sensei-record-btn button')
                   || document.querySelector('button[id*="sensei-record"]')
                   || document.querySelector('[id*="sensei-record"] button');
            console.log('[Sensei] hotkey fired:', e.code, 'btn?', !!btn);
            if (btn) btn.click();
            return;
        }

        // ? → show help
        if ((e.key === '?' || (e.shiftKey && e.code === 'Slash')) && !inField) {
            e.preventDefault();
            showHelp();
            return;
        }

        // Esc → close help (works regardless of focus)
        if (e.key === 'Escape' || e.code === 'Escape') {
            const o = document.getElementById('sensei-help-overlay');
            if (o && o.style.display !== 'none') {
                e.preventDefault();
                hideHelp();
            }
        }
    }, true);

    // Click outside the dialog (i.e. on the dimmed backdrop) → close
    document.addEventListener('click', function(e) {
        const o = document.getElementById('sensei-help-overlay');
        if (o && o.style.display !== 'none' && e.target === o) {
            hideHelp();
        }
    }, true);
}
"""


with gr.Blocks(
    title="Sensei · On-device AI Co-Teacher",
    theme=SENSEI_THEME,
    css=SENSEI_CSS,
) as app:
    # Gradio 6 injection point — js_on_load runs once when this HTML mounts.
    # The HTML body carries the help-overlay markup (hidden by default); the JS
    # binds F8 / Ctrl+Space / ? / Esc on the document level.
    overlay_html_block = gr.HTML(
        value=HOTKEY_OVERLAY_HTML.replace("__SENSEI_CSS__", SENSEI_CSS),
        js_on_load=HOTKEY_INSTALL_JS,
    )

    header_md = gr.Markdown(T("header_md"))

    with gr.Row():
        ui_language_picker = gr.Dropdown(
            label=T("ui_lang_label"),
            choices=_list_ui_languages(),
            value="zh",
            interactive=True,
            scale=1,
        )
        theme_picker = gr.Dropdown(
            label=T("theme_label"),
            choices=_list_themes(),
            value="dark",
            interactive=True,
            scale=1,
        )
        language_picker = gr.Dropdown(
            label=T("card_lang_label"),
            choices=_list_languages(),
            value="zh",
            interactive=True,
            scale=2,
        )
        template_hint = gr.Dropdown(
            label=T("tpl_hint_label"),
            choices=_list_template_hints(),
            value=TEMPLATE_HINT_AUTO,
            interactive=True,
            scale=2,
        )
        extend_source = gr.Dropdown(
            label=T("extend_label"),
            choices=_list_extend_choices(),
            value=LATEST_SENTINEL,
            interactive=True,
            scale=2,
        )

    with gr.Tabs() as tabs_root:
        with gr.Tab(T("tab_live")) as tab_live:
            live_md = gr.Markdown(T("live_md"))
            live_status = gr.Textbox(
                label=T("live_status_label"),
                value=T("live_status_idle"),
                interactive=False,
                lines=1,
            )
            live_btn = gr.Button(
                T("live_btn_idle"),
                variant="primary",
                size="lg",
                elem_id="sensei-record-btn",
            )

        with gr.Tab(T("tab_audio")) as tab_audio:
            audio_in = gr.Audio(
                sources=["microphone", "upload"],
                type="filepath",
                label=T("audio_in_label"),
            )
            with gr.Row():
                audio_btn = gr.Button(T("btn_new_card"), variant="primary", size="lg")
                audio_extend_btn = gr.Button(T("btn_extend"), variant="secondary", size="lg")

        with gr.Tab(T("tab_text")) as tab_text:
            text_in = gr.Textbox(
                label=T("text_in_label"),
                lines=3,
                placeholder=T("text_in_placeholder"),
            )
            gr.Examples(examples=EXAMPLES, inputs=text_in, label=T("examples_label"))
            with gr.Row():
                text_btn = gr.Button(T("btn_new_card"), variant="primary", size="lg")
                text_extend_btn = gr.Button(T("btn_extend"), variant="secondary", size="lg")

        with gr.Tab(T("tab_history")) as tab_history:
            history_md = gr.Markdown(T("history_md"))
            with gr.Row():
                history_dropdown = gr.Dropdown(
                    label=T("history_dropdown_label"),
                    choices=_list_history_choices(),
                    interactive=True,
                    scale=4,
                )
                history_refresh = gr.Button(T("history_refresh_btn"), scale=1)
            with gr.Row():
                with gr.Column(scale=1):
                    hist_transcript = gr.Textbox(label=T("transcript_label"), lines=3)
                    hist_json = gr.Code(label=T("json_label"), language="json")
                with gr.Column(scale=2):
                    hist_html = gr.HTML(label=T("hist_html_label"))

    with gr.Row():
        with gr.Column(scale=1):
            transcript_out = gr.Textbox(label=T("transcript_label"), lines=3)
            json_out = gr.Code(label=T("json_label"), language="json")
        with gr.Column(scale=2):
            html_out = gr.HTML(label=T("html_label"))

    with gr.Accordion(T("accordion_title"), open=True) as ops_accordion:
        with gr.Row():
            summarize_btn = gr.Button(
                T("summary_btn"),
                variant="secondary",
                size="sm",
            )
        suggestions_md = gr.Markdown(T("suggestions_md"))
        with gr.Row():
            sugg_btn_1 = gr.Button(T("suggest_btn_idle"), visible=False, variant="secondary", size="sm")
            sugg_btn_2 = gr.Button(T("suggest_btn_idle"), visible=False, variant="secondary", size="sm")
            sugg_btn_3 = gr.Button(T("suggest_btn_idle"), visible=False, variant="secondary", size="sm")

    output_targets = [transcript_out, json_out, html_out]
    dropdown_targets = [extend_source, history_dropdown]

    suggestion_buttons = [sugg_btn_1, sugg_btn_2, sugg_btn_3]

    audio_btn.click(handle_audio, [audio_in, template_hint], output_targets) \
        .then(refresh_dropdowns, None, dropdown_targets) \
        .then(update_suggestions_after_gen, None, suggestion_buttons)
    text_btn.click(handle_text, [text_in, template_hint], output_targets) \
        .then(refresh_dropdowns, None, dropdown_targets) \
        .then(update_suggestions_after_gen, None, suggestion_buttons)
    audio_extend_btn.click(
        handle_audio_extend, [audio_in, extend_source], output_targets
    ).then(refresh_dropdowns, None, dropdown_targets) \
     .then(update_suggestions_after_gen, None, suggestion_buttons)
    text_extend_btn.click(
        handle_text_extend, [text_in, extend_source], output_targets
    ).then(refresh_dropdowns, None, dropdown_targets) \
     .then(update_suggestions_after_gen, None, suggestion_buttons)

    live_outputs = [live_btn, live_status, transcript_out, json_out, html_out]
    live_btn.click(handle_live_toggle, [template_hint], live_outputs) \
        .then(refresh_dropdowns, None, dropdown_targets) \
        .then(update_suggestions_after_gen, None, suggestion_buttons)

    summarize_btn.click(handle_summarize_today, None, output_targets) \
        .then(refresh_dropdowns, None, dropdown_targets) \
        .then(update_suggestions_after_gen, None, suggestion_buttons)

    # 點擊任一建議按鈕 → 一個 handler 同時處理：生卡 + 重整下拉 + 重整建議按鈕。
    # 用單一 handler（不用 .then 鏈）避免按鈕 value 反覆替換造成的時序競態。
    suggestion_chain_outputs = output_targets + dropdown_targets + suggestion_buttons
    for sb in suggestion_buttons:
        sb.click(handle_suggestion_chain, sb, suggestion_chain_outputs)

    history_dropdown.change(
        load_history_entry,
        history_dropdown,
        [hist_transcript, hist_json, hist_html],
    )
    history_refresh.click(refresh_dropdowns, None, dropdown_targets)

    theme_picker.change(handle_theme_change, theme_picker, html_out)
    language_picker.change(handle_language_change, language_picker, html_out)

    # UI language toggle (operator-facing only) — updates many components at once.
    ui_lang_outputs = [
        header_md, live_md, history_md, suggestions_md,
        ui_language_picker, theme_picker, language_picker, template_hint, extend_source,
        tab_live, tab_audio, tab_text, tab_history,
        live_status, live_btn,
        audio_in, audio_btn, audio_extend_btn,
        text_in, text_btn, text_extend_btn,
        history_dropdown, history_refresh,
        hist_transcript, hist_json, hist_html,
        transcript_out, json_out, html_out,
        ops_accordion, summarize_btn,
        overlay_html_block,
    ]
    ui_language_picker.change(
        handle_ui_language_change, ui_language_picker, ui_lang_outputs
    )


# ────────────────────────────────────────────────────────────────────
# Second-screen / projector view — read-only fullscreen card display
#
# 設計目的：老師上課時主操作畫面在筆電（Gradio UI）；
# 接投影機的那一面用瀏覽器打開 /display，按 F11 全螢幕，
# 只看到最新的卡片，沒有任何控制元件。
# 前端用 JS 每秒輪詢 /display/data，新卡片到來時做淡入淡出。
# ────────────────────────────────────────────────────────────────────

DISPLAY_HTML = """<!doctype html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<title>Sensei · /display</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  html, body {
    margin: 0; padding: 0; height: 100%;
    background: #f6f1e6; color: #29261b;
    font-family: 'Geist', 'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif;
    transition: background 0.4s ease, color 0.4s ease;
    /* Subtle paper grain via tiny radial-gradient noise */
    background-image:
      radial-gradient(rgba(58,42,20,0.025) 1px, transparent 1px),
      radial-gradient(rgba(58,42,20,0.018) 1px, transparent 1px);
    background-size: 4px 4px, 7px 7px;
    background-position: 0 0, 2px 2px;
  }
  #header {
    position: fixed; top: 22px; left: 36px; right: 36px;
    display: flex; justify-content: space-between; align-items: baseline;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase;
    color: #7a6a52; opacity: 0.85; z-index: 10;
    pointer-events: none;
  }
  #footer {
    position: fixed; bottom: 22px; left: 36px; right: 36px;
    display: flex; justify-content: space-between; align-items: baseline;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase;
    color: #7a6a52; opacity: 0.7; z-index: 10;
    pointer-events: none;
  }
  #footer .dot { color: #4A7C59; font-size: 14px; vertical-align: middle; }
  #stage {
    padding: 80px 60px 80px;
    min-height: 100vh;
    box-sizing: border-box;
    transition: opacity 0.35s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  #stage.fading { opacity: 0; }
  #stage > div { width: 100%; max-width: 1600px; }
  #empty {
    text-align: center;
    padding-top: 30vh; font-size: 24px;
    font-family: 'Instrument Serif', serif;
    font-style: italic; letter-spacing: 0.02em;
    color: #7a6a52; opacity: 0.7;
  }
</style>
</head>
<body>
<div id="header">
  <span>SENSEI · /display</span>
  <span id="clock-readout">Lecture · --:--</span>
</div>
<div id="stage"><div id="empty">Waiting for the first card…</div></div>
<div id="footer">
  <span><span class="dot">●</span>&nbsp; ON-DEVICE · NOTHING LEAVES THE ROOM</span>
  <span>Powered by Gemma 4 + Whisper</span>
</div>
<script>
let lastId = "";
let lastTheme = "";

function tick() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  const ss = String(now.getSeconds()).padStart(2, "0");
  const el = document.getElementById("clock-readout");
  if (el) el.textContent = `Lecture · ${hh}:${mm}:${ss}`;
}
setInterval(tick, 1000);
tick();

async function poll() {
  try {
    const r = await fetch("/display/data", { cache: "no-store" });
    if (!r.ok) return;
    const d = await r.json();
    if (d.bg && d.bg !== lastTheme) {
      document.body.style.background = d.bg;
      if (d.fg) document.body.style.color = d.fg;
      lastTheme = d.bg;
    }
    if (d.id && d.id !== lastId) {
      const stage = document.getElementById("stage");
      stage.classList.add("fading");
      setTimeout(() => {
        stage.innerHTML = d.html;
        stage.classList.remove("fading");
        lastId = d.id;
      }, 320);
    }
  } catch (e) { /* network blip — silent */ }
}
setInterval(poll, 1000);
poll();
</script>
</body>
</html>
"""


def _build_fastapi_app() -> FastAPI:
    """把 Gradio 應用 mount 到 FastAPI 上，並加上 /display 與 /display/data 兩條路由。"""
    fastapi_app = FastAPI(title="Sensei")

    @fastapi_app.get("/display", response_class=HTMLResponse)
    async def display_page():
        return HTMLResponse(DISPLAY_HTML)

    @fastapi_app.get("/display/data")
    async def display_data():
        t = _theme()
        base = {"bg": t["display_bg"], "fg": t["fg"]}
        entries = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
        if not entries:
            return JSONResponse({"id": "", "html": "", **base})
        p = entries[0]
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return JSONResponse({"id": "", "html": "", **base})

        # Pick language; if non-Chinese requested but not yet cached, render Chinese
        # rather than blocking the projector poll on a Gemma 4 translate call.
        # (Operator UI's language toggle triggers caching; /display catches up.)
        target = _lang()
        if target == "zh":
            data = payload.get("data", {})
            cache_key = ""
        else:
            field = f"data_{target}"
            data = payload.get(field) or payload.get("data", {})
            cache_key = f"_{target}" if payload.get(field) else f"_pending_{target}"

        return JSONResponse({
            "id": p.stem + cache_key,  # bust cache when lang changes
            "html": render_html(data),
            **base,
        })

    return gr.mount_gradio_app(fastapi_app, app, path="/")


if __name__ == "__main__":
    fastapi_app = _build_fastapi_app()
    print()
    print("=" * 60)
    print(" Sensei serving on http://localhost:7860")
    print("   操作畫面（筆電）：    http://localhost:7860/")
    print("   第二螢幕（投影機）： http://localhost:7860/display  ← F11 全螢幕")
    print("=" * 60)
    print()
    uvicorn.run(fastapi_app, host="0.0.0.0", port=7860, log_level="warning")
