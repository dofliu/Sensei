"""
Sensei · Second-screen / projector view
================================
Serves the read-only fullscreen projector page and its data feed. The Gradio
operator console is mounted at / on the same FastAPI app.

Routes
- GET /display          fullscreen HTML page (F11 on the projector screen)
- GET /display/events   Server-Sent Events: pushes the latest card the moment
                        it changes (new card, language switch, theme switch)
- GET /display/data     one-shot JSON snapshot; the page falls back to polling
                        this every second if EventSource is unavailable

Why SSE instead of the original 1 s polling (PROPOSAL B4)
- A 50-minute lecture is ~3000 polls, each of which used to glob the history
  directory, read the newest JSON and re-render the card HTML from scratch.
  Now the server renders once per (card, language, theme) and pushes it.
- Polling is kept as a silent fallback so a browser that blocks EventSource
  (or a proxy that buffers streams) still shows cards.

設計目的：老師上課時主操作畫面在筆電（Gradio UI）；接投影機的那一面用瀏覽器打開
/display，按 F11 全螢幕，只看到最新的卡片，沒有任何控制元件。
"""

import asyncio
import json

import gradio as gr
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from core.session import latest_card
from frontend.renderers import CURRENT_THEME, _theme, render_html


# How often the SSE loop re-checks the history directory for a newer card.
SSE_CHECK_INTERVAL_S = 0.5
# Comment-only keepalive so proxies do not drop an idle stream.
SSE_KEEPALIVE_S = 15.0
# Bound on the render cache; entries are tiny HTML strings but keep it finite.
RENDER_CACHE_MAX = 64


# ────────────────────────────────────────────────────────────────────
# Latest-card resolution + render cache
# ────────────────────────────────────────────────────────────────────

_render_cache: dict[tuple, str] = {}


def _resolve_card(payload: dict, target: str) -> tuple[dict, str]:
    """Pick the card data for the requested language.

    If a non-Chinese language is requested but not yet cached in the history
    JSON, render the Chinese original rather than blocking the projector on a
    Gemma 4 translate call. (The operator UI's language toggle triggers the
    translation + caching; /display catches up on the next change event.)
    Returns (data, cache_key) where cache_key busts the client when the
    language flips.
    """
    if target == "zh":
        return payload.get("data", {}), ""
    field = f"data_{target}"
    if payload.get(field):
        return payload[field], f"_{target}"
    return payload.get("data", {}), f"_pending_{target}"


def _render_cached(key: tuple, data: dict) -> str:
    html = _render_cache.get(key)
    if html is None:
        if len(_render_cache) >= RENDER_CACHE_MAX:
            _render_cache.clear()
        html = render_html(data)
        _render_cache[key] = html
    return html


def _display_state(get_history_dir, get_lang) -> tuple[dict, str]:
    """Build the JSON the projector page consumes.

    `get_history_dir` is re-evaluated on every tick so starting a lecture
    (PROPOSAL B3) redirects the projector to that session's directory without
    restarting the stream.

    Returns (state, change_key). `change_key` folds in everything that should
    trigger a push (card id, language, theme, file mtime) while `state["id"]`
    keeps the original contract the page's fade logic relies on.
    """
    t = _theme()
    theme_name = CURRENT_THEME["name"]
    base = {"bg": t["display_bg"], "fg": t["fg"]}
    p = latest_card(get_history_dir())
    if p is None:
        return {"id": "", "html": "", **base}, f"|{theme_name}"
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
        mtime = p.stat().st_mtime_ns
    except Exception:
        return {"id": "", "html": "", **base}, f"|{theme_name}"

    target = get_lang()
    data, cache_key = _resolve_card(payload, target)
    card_id = p.stem + cache_key
    # Full path in the cache key: two lectures can hold the same card stem.
    html = _render_cached((str(p), cache_key, theme_name, mtime), data)
    return {"id": card_id, "html": html, **base}, f"{card_id}|{theme_name}|{mtime}"


async def event_stream(get_history_dir, get_lang):
    """SSE body: emit the current state immediately, then only on change.
    Keepalive comments keep proxies from closing an idle stream."""
    last_key = None
    idle = 0.0
    while True:
        state, key = _display_state(get_history_dir, get_lang)
        if key != last_key:
            last_key = key
            idle = 0.0
            yield f"data: {json.dumps(state, ensure_ascii=False)}\n\n"
        elif idle >= SSE_KEEPALIVE_S:
            idle = 0.0
            yield ": keepalive\n\n"
        await asyncio.sleep(SSE_CHECK_INTERVAL_S)
        idle += SSE_CHECK_INTERVAL_S


# ────────────────────────────────────────────────────────────────────
# Page
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
  <span id="link-readout">Powered by Gemma 4 + Whisper</span>
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

// Apply one state object from either transport (SSE push or poll).
function applyState(d) {
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
}

// Fallback transport: 1 s polling of the JSON snapshot.
let pollTimer = null;
async function poll() {
  try {
    const r = await fetch("/display/data", { cache: "no-store" });
    if (!r.ok) return;
    applyState(await r.json());
  } catch (e) { /* network blip — silent */ }
}
function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(poll, 1000);
  poll();
}

// Primary transport: Server-Sent Events. Falls back to polling for this
// page load if the stream cannot be established.
function startSSE() {
  if (!("EventSource" in window)) { startPolling(); return; }
  const es = new EventSource("/display/events");
  es.onmessage = (ev) => {
    try { applyState(JSON.parse(ev.data)); } catch (e) { /* ignore */ }
  };
  es.onerror = () => {
    es.close();
    startPolling();
  };
}
startSSE();
</script>
</body>
</html>
"""


def build_fastapi_app(gradio_app, get_history_dir, get_lang,
                      theme=None, css: str | None = None) -> FastAPI:
    """把 Gradio 應用 mount 到 FastAPI 上，並加上 /display 三條路由。
    gradio_app: the gr.Blocks instance; get_history_dir: zero-arg callable
    returning the directory the current lecture writes cards to;
    get_lang: zero-arg callable returning the current card language code;
    theme / css: forwarded to gr.mount_gradio_app (Gradio 6 moved them off
    the Blocks constructor)."""
    fastapi_app = FastAPI(title="Sensei")

    @fastapi_app.get("/display", response_class=HTMLResponse)
    async def display_page():
        return HTMLResponse(DISPLAY_HTML)

    @fastapi_app.get("/display/data")
    async def display_data():
        state, _ = _display_state(get_history_dir, get_lang)
        return JSONResponse(state)

    @fastapi_app.get("/display/events")
    async def display_events():
        return StreamingResponse(
            event_stream(get_history_dir, get_lang),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    mount_kwargs = {}
    if theme is not None:
        mount_kwargs["theme"] = theme
    if css:
        mount_kwargs["css"] = css
    return gr.mount_gradio_app(fastapi_app, gradio_app, path="/", **mount_kwargs)
