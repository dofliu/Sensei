"""
Sensei · Operator-UI strings (zh / en)
================================
Labels for the Gradio operator console only. Card *content* language is a
separate axis handled by core.llm.SenseiLLM.translate.
"""


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
        "tpl_quiz":           "📝 隨堂測驗（4 選 1）",
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
        "tpl_quiz":           "📝 Quick quiz (4-option MCQ)",
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
