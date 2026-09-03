"""
Sensei · Card renderers
================================
Pure functions: validated card dict -> HTML string. No Gradio, no models.

Owns the THEMES palette and the mutable CURRENT_THEME selector so both the
operator console and the /display projector view render identically.

Large-print rule (CLAUDE.md §3): card text >= 24 px, key headings >= 36 px.
"""


# Primary serif uses Playfair Display (multi-weight 400-900); Instrument Serif kept
# as italic-flavoured accent (single weight 400, beautiful for italic moments only).
FONT_SERIF        = "'Playfair Display', 'Noto Serif TC', Georgia, serif"
FONT_SERIF_ITALIC = "'Instrument Serif', 'Playfair Display', 'Noto Serif TC', Georgia, serif"
FONT_BODY         = "'Geist', 'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif"
FONT_MONO         = "'JetBrains Mono', Menlo, Consolas, monospace"


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


def render_quiz_card(d: dict) -> str:
    """
    Paper-editorial quiz card for projection.

    Design intent: the answer is intentionally NOT rendered on screen — students
    sitting near the projector would spoiler themselves before the teacher gets
    to lead the reveal. The teacher reads the correct answer + rationale from
    the operator UI (JSON tab on their laptop) and announces it verbally. The
    `answer` / `explanation` fields remain in the data for future reveal-toggle.

    For the same reason, all four option cards are styled identically — no
    visual highlight on the correct one.
    """
    t = _theme()
    accents = t["accents"]
    fg_strong = t["fg_strong"]
    fg_muted = t["fg_muted"]
    card_bg = t["card_bg"]
    card_border = t["card_border"]

    options = d.get("options", []) or []
    # Defensive padding so a partial LLM output still renders something coherent
    while len(options) < 4:
        options.append("—")
    labels = ["A", "B", "C", "D"]

    mono_label_style = (
        f"font-family:{FONT_MONO};font-size:15px;font-weight:500;"
        f"letter-spacing:0.18em;text-transform:uppercase;color:{fg_muted};"
    )

    difficulty = (d.get("difficulty") or "medium").lower()
    diff_label = {"easy": "EASY", "medium": "MEDIUM", "hard": "HARD"}.get(difficulty, "MEDIUM")
    badge_html = (
        f"<div style='{mono_label_style}margin-bottom:20px;'>"
        f"<span style='color:{accents[0]};font-size:16px;'>●</span>&nbsp; "
        f"QUIZ · {diff_label}</div>"
    )

    option_cards = []
    for i, opt in enumerate(options[:4]):
        c = accents[i % len(accents)]
        option_cards.append(
            f"<div style='background:{card_bg};border:1px solid {card_border};"
            f"border-radius:14px;padding:32px 36px;display:flex;align-items:center;gap:28px;"
            f"box-shadow:0 1px 2px rgba(15,13,10,0.05),0 2px 6px rgba(15,13,10,0.04);'>"
            f"<div style='font-family:{FONT_SERIF_ITALIC};font-size:72px;font-weight:500;"
            f"font-style:italic;color:{c};line-height:1;min-width:64px;text-align:center;'>"
            f"{labels[i]}</div>"
            f"<div style='font-family:{FONT_BODY};font-size:38px;color:{fg_strong};"
            f"line-height:1.3;font-weight:500;'>{opt}</div>"
            f"</div>"
        )

    title_html = ""
    if d.get("title"):
        title_html = (
            f"<div style='font-family:{FONT_SERIF};font-size:44px;font-weight:500;"
            f"color:{fg_muted};margin-bottom:22px;line-height:1.15;"
            f"letter-spacing:-0.015em;font-style:italic;'>{d['title']}</div>"
        )

    return (
        f"<div style='{_container_style()}'>"
        f"{badge_html}"
        f"{title_html}"
        f"<div style='font-family:{FONT_SERIF};font-size:60px;font-weight:500;"
        f"color:{fg_strong};margin-bottom:40px;line-height:1.25;letter-spacing:-0.01em;'>"
        f"{d.get('question','')}</div>"
        f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:22px;'>"
        f"{''.join(option_cards)}</div>"
        f"</div>"
    )


RENDERERS = {
    "enumeration_cards": render_enumeration_cards,
    "comparison_table":  render_comparison_table,
    "flow_diagram":      render_flow_diagram,
    "hierarchy_tree":    render_hierarchy_tree,
    "swot":              render_swot,
    "pyramid":           render_pyramid,
    "quiz_card":         render_quiz_card,
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
