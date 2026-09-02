"""
Sensei · Second-screen / projector view
================================
Serves /display (read-only fullscreen HTML) and /display/data (latest card
JSON+HTML). The Gradio operator console is mounted at / on the same FastAPI app.
"""

import json
from pathlib import Path

import gradio as gr
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from frontend.renderers import _theme, render_html


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


def build_fastapi_app(gradio_app, history_dir: Path, get_lang) -> FastAPI:
    """把 Gradio 應用 mount 到 FastAPI 上，並加上 /display 與 /display/data 兩條路由。
    gradio_app: the gr.Blocks instance; history_dir: where cards are saved;
    get_lang: zero-arg callable returning the current card language code."""
    fastapi_app = FastAPI(title="Sensei")

    @fastapi_app.get("/display", response_class=HTMLResponse)
    async def display_page():
        return HTMLResponse(DISPLAY_HTML)

    @fastapi_app.get("/display/data")
    async def display_data():
        t = _theme()
        base = {"bg": t["display_bg"], "fg": t["fg"]}
        entries = sorted(history_dir.glob("*.json"), reverse=True)
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
        target = get_lang()
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

    return gr.mount_gradio_app(fastapi_app, gradio_app, path="/")
