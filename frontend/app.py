r"""
Sensei · Operator console (Gradio)
================================
Run:   python -m frontend.app        (or .\start_sensei.ps1 on Windows)
Open:  http://localhost:7860          operator console (teacher's laptop)
       http://localhost:7860/display  projector view (F11 fullscreen)

This file owns the Gradio Blocks layout, the event handlers and history
persistence. The pieces it used to inline now live next door:
- frontend/renderers.py  THEMES + the 7 card renderers (pure dict -> HTML)
- frontend/i18n.py       operator-UI strings (zh / en)
- frontend/display.py    /display page, SSE feed, FastAPI mount

Input modes: live microphone (F8 toggle), audio file / browser recording,
text (for testing). Every card is saved to history/ and pushed to /display.
"""

import json
import sys
from collections import deque
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

from core import session
from core.live_mic import ContinuousListener, LiveMicCapture
from core.pipeline import GATE_MIN_CONTENT, SenseiPipeline
from core.glossary import list_glossaries
from frontend.renderers import THEMES, CURRENT_THEME, render_html
from frontend.i18n import CURRENT_UI_LANG, T, _list_ui_languages
from frontend.display import build_fastapi_app
from frontend.handout import build_handout


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


def _list_glossaries() -> list:
    """課程詞彙表下拉：[(title, id)]，來源 glossaries/*.txt。"""
    return [(g.title, g.id) for g in list_glossaries()]


def _list_lecture_languages() -> list:
    return [
        (T("lect_zh"),   "zh"),
        (T("lect_en"),   "en"),
        (T("lect_auto"), "auto"),
    ]


def _list_themes() -> list:
    return [
        (T("theme_dark"),  "dark"),
        (T("theme_light"), "light"),
        (T("theme_paper"), "paper"),
    ]


# ────────────────────────────────────────────────────────────────────
# History persistence
# ────────────────────────────────────────────────────────────────────

HISTORY_DIR = Path(__file__).parent.parent / "history"
HISTORY_DIR.mkdir(exist_ok=True)


def _history_dir() -> Path:
    """Where cards are written and read right now (PROPOSAL B3).

    The active lecture's directory once the teacher presses "start lecture",
    the history root otherwise. Everything that used to touch HISTORY_DIR
    directly goes through here so /display, the history dropdown, "extend"
    and the summary all stay inside one lecture.
    """
    return session.current_dir(HISTORY_DIR)


def _cards(newest_first: bool = True) -> list[Path]:
    """Card JSONs of the current lecture; session metadata excluded."""
    files = session.card_files(_history_dir())
    return list(reversed(files)) if newest_first else files

LATEST_SENTINEL = "__latest__"
TEMPLATE_HINT_AUTO = "__auto__"


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
        (T("tpl_quiz"),    "quiz_card"),
        (T("tpl_key_fact"), "key_fact"),
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
    entries = _cards()
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
        entries = _cards()
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
    out_dir = _history_dir()
    json_path = out_dir / f"{base}.json"
    n = 1
    while json_path.exists():
        # Two cards within the same second must not overwrite each other.
        n += 1
        json_path = out_dir / f"{base}_{n}.json"
    base = json_path.stem
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
    (out_dir / f"{base}.html").write_text(standalone, encoding="utf-8")
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


def handle_glossary_change(glossary_id: str):
    """切課程詞彙表：只影響之後的 ASR，不重算既有卡片。"""
    if glossary_id:
        pipeline.set_glossary(glossary_id)


def handle_lecture_language_change(lang_value: str):
    """切授課語言：Whisper 語言 + Gemma 4 產卡語言一起換。"""
    if lang_value in ("zh", "en", "auto"):
        pipeline.set_lecture_language(lang_value)


def handle_theme_change(theme_name: str):
    """切主題：套用後立刻重新渲染最新一張卡片到操作畫面；/display 下次輪詢時自動換色。"""
    if theme_name in THEMES:
        CURRENT_THEME["name"] = theme_name
    entries = _cards()
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
    entries = _cards()
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
    active = session.current()
    if active is not None:
        # A lecture directory holds exactly one lecture — no date filter needed.
        files = session.card_files(active.dir)
        today = active.date
    else:
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


# ────────────────────────────────────────────────────────────────────
# Continuous listening (PROPOSAL B1)
# ────────────────────────────────────────────────────────────────────
# The listener's worker thread produces cards on its own; /display picks them
# up over SSE without anyone touching the console. What the console adds is
# the part students must NOT see: which utterances were skipped and why
# (PROPOSAL §3 Q4). A gr.Timer polls this log while listening.

CONTINUOUS_LOG_MAX = 10
CONTINUOUS_LOG: deque = deque(maxlen=CONTINUOUS_LOG_MAX)
# Whole-lecture tallies; CONTINUOUS_LOG only keeps the last few lines.
CONTINUOUS_COUNTS = {"cards": 0, "skipped": 0, "dropped_s": 0.0}

GATE_LABELS = {
    "card":        "gate_card",
    "no-card":     "gate_no_card",
    "too-short":   "gate_too_short",
    "quiz-phrase": "gate_quiz",
    "operator":    "gate_card",
    "raw":         "gate_card",
    "error":       "gate_error",
    "dropped":     "gate_dropped",
}


def _log_utterance(gate: str, transcript: str, note: str = "") -> None:
    CONTINUOUS_LOG.appendleft((
        datetime.now().strftime("%H:%M:%S"), gate, (transcript or "").strip(), note,
    ))


def _log_skipped(transcript: str, gate: str, reason: str, **extra) -> None:
    """Append the skip to skipped.jsonl in the lecture directory.

    Not a card, so it never reaches /display — but it is exactly the data the
    C2 bench needs to answer "how often is the gate wrong?", and it is cheap
    to write. .jsonl, so session.card_files() ignores it.

    Dropped utterances go here too, under gate="dropped". Without that a drop
    leaves no trace at all — no card, no skip — and the lecture's record
    quietly omits something the teacher said.
    """
    line = json.dumps({
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "gate": gate, "reason": reason, "transcript": transcript, **extra,
    }, ensure_ascii=False)
    try:
        with (_history_dir() / "skipped.jsonl").open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"[Sensei] could not log skipped utterance: {e}", flush=True)


def _timing(result: dict, queued_s: float) -> dict:
    """The three numbers that say where a lecture's time went."""
    return {
        "audio_s": result.get("_audio_s", 0),
        "queue_ms": int(queued_s * 1000),
        "asr_ms": result.get("_asr_ms", 0),
        "llm_ms": result.get("_llm_ms", 0),
    }


def _log_dropped(lost_s: float) -> None:
    """The queue threw away an utterance before it was ever transcribed."""
    CONTINUOUS_COUNTS["dropped_s"] = round(
        CONTINUOUS_COUNTS["dropped_s"] + lost_s, 1)
    _log_skipped("", "dropped", f"{lost_s:.1f}s never transcribed",
                 audio_s=round(lost_s, 1))
    _log_utterance("dropped", "", f"{lost_s:.1f}s lost — pipeline behind")


def _on_continuous_utterance(audio, samplerate: int, queued_s: float = 0.0) -> None:
    """Runs on the listener's worker thread, one utterance at a time."""
    try:
        result = pipeline.process_utterance_audio(audio, sample_rate=samplerate)
    except Exception as e:
        print(f"[Sensei] continuous utterance failed: {e}", flush=True)
        _log_utterance("error", "", str(e)[:60])
        return
    transcript = result.pop("_transcript", "")
    gate = result.get("_gate", "?")
    timing = _timing(result, queued_s)
    took = f"{timing['asr_ms'] + timing['llm_ms']} ms"
    if result.get("template") == "no_card":
        reason = result.get("reason", "")
        CONTINUOUS_COUNTS["skipped"] += 1
        _log_skipped(transcript, gate, reason, **timing)
        # The rule layer's reason just restates the label; show the measured
        # content length instead, which is the number the teacher would tune.
        note = f"{result.get('_content', 0)} < {GATE_MIN_CONTENT}" if gate == "too-short" else reason
        _log_utterance(gate, transcript, f"{note} · {took}")
        return
    saved = _save_to_history(result, transcript)
    _translate_and_persist(result, saved)
    CONTINUOUS_COUNTS["cards"] += 1
    _log_utterance(gate, transcript, f"{result.get('template', '')} · {took}")


continuous = ContinuousListener(_on_continuous_utterance, on_dropped=_log_dropped)


def _continuous_status() -> str:
    st = continuous.stats
    if not continuous.running and not any(st.values()):
        return T("cont_status_idle")
    key = "cont_status_running" if continuous.running else "cont_status_stopped"
    return T(key).format(
        cards=CONTINUOUS_COUNTS["cards"],
        skipped=CONTINUOUS_COUNTS["skipped"],
        short=st["too_short"],
        dropped=st["dropped"],
        dropped_s=st.get("dropped_s", 0),
    )


def _continuous_log_md() -> str:
    if not CONTINUOUS_LOG:
        return T("cont_log_empty")
    lines = [f"**{T('cont_log_title')}**", ""]
    for ts, gate, text, note in CONTINUOUS_LOG:
        label = T(GATE_LABELS.get(gate, "gate_card"))
        mark = "·" if gate in ("no-card", "too-short", "error") else "▸"
        body = text if len(text) <= 46 else text[:46] + "…"
        suffix = f" — {note}" if note else ""
        lines.append(f"<small>`{ts}` {mark} **{label}**{suffix} · {body or '—'}</small><br>")
    return "\n".join(lines)


def handle_continuous_toggle():
    """開始 / 停止連續聆聽。卡片由 worker 執行緒自己產生並推到 /display；
    這裡只負責按鈕、狀態與操作端的跳過紀錄。"""
    if continuous.running:
        continuous.stop()
    else:
        CONTINUOUS_LOG.clear()
        for k in continuous.stats:
            continuous.stats[k] = 0
        for k in CONTINUOUS_COUNTS:
            CONTINUOUS_COUNTS[k] = 0
        continuous.start()
    running = continuous.running
    return (
        gr.update(value=T("cont_btn_running") if running else T("cont_btn_idle"),
                  variant="stop" if running else "secondary"),
        _continuous_status(),
        _continuous_log_md(),
        gr.Timer(active=running),
    )


# The console mirrors /display, but only when the card actually changed —
# re-rendering the same card every 2 s is what B4 removed from the projector.
CONTINUOUS_SHOWN = {"stem": ""}


def refresh_continuous():
    """gr.Timer tick while listening: status, skip log, newest card."""
    status, log = _continuous_status(), _continuous_log_md()
    entries = _cards()
    if not entries or entries[0].stem == CONTINUOUS_SHOWN["stem"]:
        return status, log, gr.update()
    try:
        payload = json.loads(entries[0].read_text(encoding="utf-8"))
        html = render_html(_resolve_payload_for_lang(payload, entries[0]))
    except Exception as e:
        print(f"[Sensei] continuous refresh failed: {e}", flush=True)
        return status, log, gr.update()
    CONTINUOUS_SHOWN["stem"] = entries[0].stem
    return status, log, html


# ────────────────────────────────────────────────────────────────────
# Lecture sessions + handout export (PROPOSAL B3)
# ────────────────────────────────────────────────────────────────────

def _handout_strings() -> dict:
    """Operator-UI language decides what language the handout is written in."""
    return {
        "title":      T("ho_title"),
        "summary":    T("ho_summary"),
        "card":       T("ho_card"),
        "transcript": T("ho_transcript"),
        "generated":  T("ho_generated"),
        "cards_n":    T("ho_cards_n"),
    }


def _session_status_md(extra: str = "") -> str:
    """One markdown line describing where cards are currently going."""
    active = session.current()
    if active is None:
        base = T("session_none")
    else:
        base = T("session_active").format(
            course=active.course, dir=active.dir.name,
            n=len(session.card_files(active.dir)),
        )
    return f"{base}\n\n{extra}" if extra else base


def handle_session_toggle(course: str):
    """開始上課 / 結束這堂課。開課後所有卡片、歷史、總結、/display 都限定在
    history/<date>_<course>/ 之內。"""
    if session.current() is not None:
        ended = session.end()
        status = _session_status_md(
            T("session_ended").format(course=ended.course) if ended else ""
        )
    elif not (course or "").strip():
        return (
            gr.update(),
            _session_status_md(T("err_no_course")),
            *refresh_dropdowns(),
        )
    else:
        session.start(course)
        status = _session_status_md()
    label = T("session_end_btn") if session.current() else T("session_start_btn")
    return (
        gr.update(value=label,
                  variant="stop" if session.current() else "primary"),
        status,
        *refresh_dropdowns(),
    )


def handle_export_handout():
    """把目前這堂課（沒開課就是 history/ 根目錄）輸出成一份 handout.html。"""
    active = session.current()
    out_dir = _history_dir()
    try:
        path = build_handout(
            out_dir,
            course=active.course if active else "",
            date=active.date if active else datetime.now().strftime("%Y%m%d"),
            strings=_handout_strings(),
        )
    except Exception as e:
        print(f"[Sensei] handout export failed: {e}", flush=True)
        return gr.update(visible=False), _session_status_md(f"❗ {e}")
    if path is None:
        return gr.update(visible=False), _session_status_md(T("err_no_cards"))
    return (
        gr.update(value=str(path), visible=True),
        _session_status_md(T("handout_done").format(path=path)),
    )


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
        gr.update(label=T("glossary_label")),                                    # glossary_picker
        gr.update(label=T("lecture_lang_label"), choices=_list_lecture_languages()),  # lecture_lang_picker
        # Lecture session row
        gr.update(label=T("course_label"), placeholder=T("course_placeholder")),  # course_name
        gr.update(value=T("session_end_btn") if session.current() else T("session_start_btn")),
        gr.update(value=T("handout_btn")),                        # handout_btn
        gr.update(value=_session_status_md()),                    # session_status
        gr.update(label=T("handout_file_label")),                 # handout_file
        # Tabs (label = tab title)
        gr.update(label=T("tab_live")),                           # tab_live
        gr.update(label=T("tab_audio")),                          # tab_audio
        gr.update(label=T("tab_text")),                           # tab_text
        gr.update(label=T("tab_history")),                        # tab_history
        # Live tab specifics
        gr.update(label=T("live_status_label"),
                  value=T("live_status_recording") if live_mic.recording else T("live_status_idle")),
        gr.update(value=T("live_btn_recording") if live_mic.recording else T("live_btn_idle")),
        # Continuous listening block
        gr.update(value=T("cont_md")),                            # cont_md
        gr.update(value=T("cont_btn_running") if continuous.running else T("cont_btn_idle")),
        gr.update(label=T("cont_status_label"), value=_continuous_status()),
        gr.update(value=_continuous_log_md()),                    # cont_log
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
    entries = _cards()
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
    if continuous.running:
        # F8 while continuous listening: cut the current utterance now instead
        # of waiting for the silence hangover (PROPOSAL B1 manual override).
        continuous.flush_now()
        return (
            gr.update(),
            T("live_status_flushed"),
            gr.update(), gr.update(), gr.update(),
        )
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


with gr.Blocks(title="Sensei · On-device AI Co-Teacher") as app:
    # theme / css are passed to gr.mount_gradio_app in __main__ (Gradio 6 moved
    # them off the Blocks constructor). SENSEI_CSS is additionally injected via
    # the overlay HTML block so it survives any launch path.
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

    # Course settings (PROPOSAL B2): which glossary Whisper is primed with, and
    # what language the lecture is in. Both apply to every input mode.
    with gr.Row():
        glossary_choices = _list_glossaries()
        glossary_picker = gr.Dropdown(
            label=T("glossary_label"),
            choices=glossary_choices,
            value=glossary_choices[0][1] if glossary_choices else None,
            interactive=True,
            scale=3,
        )
        lecture_lang_picker = gr.Dropdown(
            label=T("lecture_lang_label"),
            choices=_list_lecture_languages(),
            value="zh",
            interactive=True,
            scale=2,
        )

    # Lecture session (PROPOSAL B3): one directory per lecture, one handout
    # per lecture. Without it every course of the day lands in one pile.
    with gr.Row():
        course_name = gr.Textbox(
            label=T("course_label"),
            placeholder=T("course_placeholder"),
            lines=1,
            scale=3,
        )
        session_btn = gr.Button(T("session_start_btn"), variant="primary", scale=1)
        handout_btn = gr.Button(T("handout_btn"), variant="secondary", scale=1)
    session_status = gr.Markdown(_session_status_md())
    handout_file = gr.File(label=T("handout_file_label"), visible=False)

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

            # Continuous listening (PROPOSAL B1) — press once per lecture.
            cont_md = gr.Markdown(T("cont_md"))
            cont_btn = gr.Button(T("cont_btn_idle"), variant="secondary", size="lg")
            cont_status = gr.Textbox(
                label=T("cont_status_label"),
                value=T("cont_status_idle"),
                interactive=False,
                lines=1,
            )
            cont_log = gr.Markdown(T("cont_log_empty"))
            # Only ticks while listening; handle_continuous_toggle flips it.
            cont_timer = gr.Timer(2.0, active=False)

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

    cont_btn.click(
        handle_continuous_toggle, None,
        [cont_btn, cont_status, cont_log, cont_timer],
    )
    cont_timer.tick(refresh_continuous, None, [cont_status, cont_log, html_out])

    session_btn.click(
        handle_session_toggle, course_name,
        [session_btn, session_status] + dropdown_targets,
    )
    handout_btn.click(handle_export_handout, None, [handout_file, session_status])

    theme_picker.change(handle_theme_change, theme_picker, html_out)
    glossary_picker.change(handle_glossary_change, glossary_picker, None)
    lecture_lang_picker.change(handle_lecture_language_change, lecture_lang_picker, None)
    language_picker.change(handle_language_change, language_picker, html_out)

    # UI language toggle (operator-facing only) — updates many components at once.
    ui_lang_outputs = [
        header_md, live_md, history_md, suggestions_md,
        ui_language_picker, theme_picker, language_picker, template_hint, extend_source,
        glossary_picker, lecture_lang_picker,
        course_name, session_btn, handout_btn, session_status, handout_file,
        tab_live, tab_audio, tab_text, tab_history,
        live_status, live_btn,
        cont_md, cont_btn, cont_status, cont_log,
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


if __name__ == "__main__":
    fastapi_app = build_fastapi_app(
        app, _history_dir, _lang, theme=SENSEI_THEME, css=SENSEI_CSS,
    )
    print()
    print("=" * 60)
    print(" Sensei serving on http://localhost:7860")
    print("   操作畫面（筆電）：    http://localhost:7860/")
    print("   第二螢幕（投影機）： http://localhost:7860/display  ← F11 全螢幕")
    print("=" * 60)
    print()
    uvicorn.run(fastapi_app, host="0.0.0.0", port=7860, log_level="warning")
