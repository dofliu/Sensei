# Sensei · 賽後強化提案（v1 → v2）

> **對象**：劉瑞弘老師 + 後續接手的 Claude Code session
> **日期**：2026-09-02
> **前提**：Gemma 4 Good Hackathon 已於 2026-05-18 截止。本文件不再以「demo 影片」為唯一標準，改以 **「老師每週真的在課堂上用」** 為標準。CLAUDE.md §1A 的 hackathon 評分邏輯已完成階段性任務，這份提案取代 CLAUDE.md §7–§8 作為下一階段的工作依據。
> **依據**：以 `main` 分支 `f40343f`（2026-05-11）的實際程式碼盤點，不是憑印象。
> **執行狀態（2026-09-03）**：**Phase A 與 Phase B 全部落地**（B5 拆檔、B4 SSE、B2 詞彙表 + 語言、B3 session + 講義匯出、B1 連續聆聽 + `no_card` 閘門）。§3 的六個問題採用本文的建議值。CLAUDE.md 已改寫為賽後版。
>
> **但整個 v2 還沒在實機跑過**：所有驗證都在沒有 GPU / Ollama / 麥克風的 Linux sandbox 用 stub 完成。下一步不是再寫功能，是 `.\dry_run.ps1`（現在 9 步，第 8 步不需要載模型）＋ 一堂真實的課，然後**用那堂課的觀察去調 B1 的切句參數**——它們現在是本文的建議值，不是量出來的。`python -m bench.segmenter_probe` 可以在沒有麥克風的情況下看到改一個常數的效果。
>
> **B1 與本文設計的唯一差異**：切句用能量門檻 + 自適應噪音底，不是直接串流 Silero。理由是 faster-whisper 的 Silero 包裝是內部 API、版本間換過形狀，逐格串流會把 Sensei 綁死在那個形狀上；而 `transcribe_array` 本來就帶 `vad_filter=True`，Silero 仍然在每一段內部濾非語音。能量決定「一段講到哪裡結束」，Silero 決定「這段裡哪些是語音」。

---

## 0. TL;DR

Sensei v1 的功能面已經完整（7 模板、tool-calling + JSON 雙路徑、Live mic、`/display`、8 語翻譯、延伸卡片、今日總結）。賽後要解決的不是「功能不夠」，而是三件事：

| # | 問題 | 一句話 |
|---|---|---|
| 1 | **課堂操作成本** | 老師每講一段就要按一次 F8 開、一次 F8 關。一堂 50 分鐘的課要按幾十次，這是真實使用的最大摩擦。 |
| 2 | **單一領域、單一語言** | ASR 詞彙表只有自動控制；`language="zh"` 寫死。換一門課或換一位老師就要改程式碼。 |
| 3 | **文件與程式碼已脫節** | README / CONTRIBUTING / 模組 docstring 對模板數量、Phase 2、Python 版本各說各話；hackathon 時程表停在 Day 5。 |

**建議順序**：先花一週收尾（Phase A），再做「連續聆聽」與「多領域詞彙表」（Phase B），最後才碰學生端互動與評測（Phase C）。UI 全面改寫（`UI_migration_proposal.md` 的 Pass 2）**不建議**在 Phase B 之前動。

---

## 1. 現況盤點（來自程式碼）

### 1.1 已經穩定、不要動的部分

| 模組 | 狀態 | 備註 |
|---|---|---|
| `core/llm.py::structurize` | 穩 | tools 主路徑 → JSON-mode 備援 → Pydantic 嚴格 → 寬鬆 salvage，四層防線。`_path` / `_salvaged` 都寫進 history JSON，可事後統計。 |
| `core/templates.py` | 穩 | 7 個 schema，`TEMPLATE_REGISTRY` 同時餵 tools spec 與驗證。 |
| `core/pipeline.py` | 穩 | `QUIZ_TRIGGER_PHRASES` 語音觸發只在 Auto 模式生效，操作者選擇優先。 |
| `/display` 投影視圖 | 穩 | Paper editorial 版面、1 秒輪詢、淡入淡出。 |
| 翻譯快取 | 穩 | 每張卡片的翻譯存回同一個 history JSON（`data_en` 等欄位），投影端不會被翻譯呼叫卡住。 |

### 1.2 程式碼裡看得到的技術債（依影響排序）

| # | 位置 | 問題 | 影響 |
|---|---|---|---|
| D1 | `frontend/app.py`（1975 行） | 渲染器、主題、i18n 字典、操作 handler、`DISPLAY_HTML`、FastAPI 掛載全在一個檔案 | 任何改動都要在同一個檔案裡找位置；新人與 AI 助手都難以定位。**不是**要大重構，只要拆成 3 個檔案（見 §3）。 |
| D2 | `_build_fastapi_app::display_data` | 每秒一次 `HISTORY_DIR.glob` + 讀檔 + `render_html()` 全量重算，即使卡片沒變 | 現在不痛，但一堂課 3000 次輪詢全部白算；投影機端若換成低階筆電會有感。 |
| D3 | `core/asr.py::ASRConfig` | `LANGUAGE = "zh"` 與 `INITIAL_PROMPT` 皆為類別常數，無法在 UI 或設定檔切換 | 換課、換語言都要改 `.py`。與「任何老師都能用」的定位矛盾。 |
| D4 | `core/live_mic.py` | 純 toggle 錄音：按一次開始、按一次結束，整段一次送 ASR | 老師必須主動「決定這一段要卡片」。一段講 40 秒就要等 40 秒 + ASR + LLM 才看到卡片。 |
| D5 | `frontend/app.py` 全域狀態 | `CURRENT_THEME` / `CURRENT_LANG` / `CURRENT_UI_LANG` 都是模組層級可變 dict | 單人單機沒問題（也是設計），但表示 `/display` 與操作端永遠共用同一組狀態，未來若要「投影英文、操作端中文」就要改。 |
| D6 | `core/llm.py::_salvage_card_data` | `comparison_table` 與 `hierarchy_tree`、`quiz_card` 沒有 salvage 分支 | 這三種模板在 e2b 掉欄位時直接退回 JSON-mode，多一次 LLM 呼叫（~1–2 秒）。quiz_card 的 `explanation` / `difficulty` 有預設值理論上可補。 |
| D7 | `requirements.txt` | 只有下限版本（`gradio>=5.0.0`），實際跑在 Gradio 6 | 下次 `pip install` 可能又踩到 API 變動（5 月就中過一次）。 |
| D8 | `history/` | 用檔名時間戳排序取「最新」，沒有 session 概念 | 「今日總結」靠日期字串過濾；一天兩門課會混在一起。 |

### 1.3 文件脫節清單（Phase A 直接修）

| 檔案 | 現況 | 應為 |
|---|---|---|
| `core/templates.py` docstring | 「4 visualization templates」 | 7 |
| `CONTRIBUTING.md` | 「Six Pydantic schemas」、「existing six」 | 7 |
| `README.md` §Why Gemma 4 第 4 點 | 「Phase 2 will add image input（webcam → whiteboard）」 | 與 `WRITEUP.md` §8 矛盾（已評估後擱置）。二選一，建議跟 WRITEUP 一致。 |
| `README.md` §Screenshots | 「4 stills… captured during the Day 7 shoot」、影片連結待補 | 補上實際截圖與 YouTube 連結，或改寫成賽後版。 |
| `docs/screenshots/README.md` | 列出 4 個不存在的 PNG 檔名 | 對齊實際檔案 |
| `README.md` §9-day plan | Day 6–10 未勾選 | 改為「Hackathon 歷程」段落，記錄結果 |
| `requirements.txt` vs `CONTRIBUTING.md` | Python 3.11+ vs 3.12+ | 統一為 3.12（使用者環境） |
| `frontend/app.py` 檔頭 docstring | 「4 template renderers」、「MVP UI」 | 7；已非 MVP |
| `CLAUDE.md` §1 / §7 / §8 | 狀態停在 2026-05-11 | 改寫為賽後版；hackathon 規則段落（§1A）移到附錄保留 |

---

## 2. 提案：三個 Phase

### 判準（取代 CLAUDE.md §1A 的四問）

1. 老師**下週上課**會不會因此少做一件事？→ BUILD
2. 換一位老師、換一門課，**不改程式碼**就能用？→ BUILD
3. 能不能產生**可以寫進論文**的數據？→ 排 Phase C
4. 只有工程師會注意到？→ DEFER

### Phase A · 收尾與封存（約 1 週，低風險）

| 項目 | 內容 | 產出 |
|---|---|---|
| A1 | §1.3 文件同步 | 8 個檔案的小修 |
| A2 | Hackathon 結果記錄 | `README.md` 加「Hackathon 歷程」段（結果、影片連結、截圖）；`WRITEUP.md` 凍結不再改 |
| A3 | 釘住依賴版本 | `requirements.txt` 改成 `gradio==6.x.y`、`faster-whisper==…`（以使用者機器上實際 `pip freeze` 為準） |
| A4 | `history/` 加 `.gitignore` 確認 | 避免課堂逐字稿意外進 repo（隱私是 Sensei 的核心主張，repo 自己不能違反） |
| A5 | 一鍵啟動腳本 | `start_sensei.ps1`：檢查 Ollama 在跑、模型已 pull、啟動 app、自動開兩個瀏覽器分頁（`/` 與 `/display`）。沿用 `dry_run.ps1` 的 ASCII-only 寫法。 |

### Phase B · 課堂可用性（約 3 週，中風險，這是 v2 的主體）

#### B1. 連續聆聽模式（解 D4）

**目標**：老師按一次「開始上課」，之後不再碰鍵盤。Sensei 自己切句、自己判斷哪些段落值得出卡片。

設計：

```
sounddevice 串流 (16 kHz)
   → Silero VAD（faster-whisper 已內建，零新依賴）
   → 靜音 ≥ 1.2 s 視為一段（utterance）
   → 段長 < 3 s 直接丟棄（「好」「對」「下一頁」）
   → ASR 該段
   → 「值得出卡片嗎」閘門（見下）
   → structurize → history → /display
```

「值得出卡片嗎」閘門是關鍵，否則每句話都出卡片，投影機會閃到學生頭暈。兩層：

1. **規則層（免 LLM）**：段落字數 < 15 字 → 不出卡；含 `QUIZ_TRIGGER_PHRASES` → 必出卡。
2. **模型層**：tools 路徑加一個第 8 個工具 `no_card`（描述：「這段話沒有可視覺化的結構，例如閒聊、過場、點名」）。模型選 `no_card` 就跳過。這比另外跑一次分類便宜，而且沿用現有 tool-calling 架構。

保留 F8 作為手動覆寫（強制把「上一段」出卡片，或強制結束當前段）。

風險與對策：

| 風險 | 對策 |
|---|---|
| Whisper large-v3 對 3–8 秒短段落的準確率下降 | 段落合併：靜音 < 1.2 s 但累積 < 25 s 就繼續累積；上限 25 s 強制切 |
| ASR + LLM 排隊，投影機落後講課 30 秒 | 單一 worker queue，佇列長度 > 2 就丟最舊的段（老師已經講過去了，卡片晚到反而干擾） |
| `no_card` 誤判率 | history JSON 記錄 `_gate` 決策，跑幾堂課後看數據再調（餵 Phase C 的 C2） |

**不做**：瀏覽器端 `MediaRecorder`。`live_mic.py` 的 server-side 設計理由仍然成立（麥克風就在同一台筆電）。

#### B2. 多領域詞彙表與語言切換（解 D3）

```
glossaries/
  auto_control.zh.txt     ← 現在 ASRConfig.INITIAL_PROMPT 的內容搬過來
  machine_learning.zh.txt
  wind_energy.zh.txt
  _template.txt           ← 給其他老師複製用的空白範本
```

- `ASRConfig` 改成從檔案讀 `INITIAL_PROMPT`；操作端加「課程詞彙表」下拉（沿用 `template_hint` 下拉的寫法）。
- `LANGUAGE` 開放 `zh` / `en` / `auto`。`auto` 交給 Whisper 偵測，但要在 UI 明示「中英夾雜請選 zh」。
- 順手把 `prompts/classifier.txt` 的「繁體中文」規則參數化：英文授課時卡片內容應該直接是英文，而不是先中文再翻譯。

這一項直接對應 CONTRIBUTING.md 說「最歡迎的貢獻是詞彙表」，但現在貢獻者得改 Python 檔。

#### B3. 講義輸出（把 history 變成資產）

現在 `history/` 每張卡都有 `.json` + `.html`，`summarize_session` 也能出今日總結，但都停在單張卡片。加：

- **Session 概念**（解 D8）：「開始上課」時建立 `history/2026-09-10_自動控制_第3週/`，該堂課所有卡片進同一個目錄。
- **匯出**：一鍵產生一份 `handout.html`（所有卡片按時間排 + 今日總結在最前 + 每張卡對應的逐字稿摺疊在下方）。老師課後丟到教學平台，學生拿到的就是那堂課的結構化筆記。
- PDF 用瀏覽器列印即可，不加依賴。

這是 Sensei 從「上課工具」變成「課後也有價值」最便宜的一步，也是 Future of Education 敘事的自然延伸。

#### B4. `/display` 改推播 + 渲染快取（解 D2）

- `_save_to_history` 已經寫了 `.html`，`display_data` 直接讀那個檔案，不再每次 `render_html()`。
- 輪詢改 SSE（FastAPI `StreamingResponse`，20 行內）。瀏覽器端 `EventSource` 取代 `setInterval(poll, 1000)`。輪詢邏輯保留作備援（SSE 斷線時自動退回）。
- 翻譯切換時 SSE 推一次新 id 即可，行為與現在一致。

小改動，但 B1 上線後投影更新頻率會變高，先做這個再做 B1 比較穩。

#### B5. `app.py` 三分法（解 D1，配合 B1–B4 順手做，不獨立做）

```
frontend/
  app.py          ← Gradio Blocks + handlers（留 ~700 行）
  renderers.py    ← THEMES + 7 個 render_* + render_html + _lucide_svg
  display.py      ← DISPLAY_HTML + _build_fastapi_app + SSE
  i18n.py         ← UI_TEXTS + T()
```

規則：**只搬、不改行為**，每搬一個檔案就跑一次 `dry_run.ps1`。CLAUDE.md §9「不為了乾淨而重構」在這裡的例外理由是：B1–B4 都要改 `app.py`，先拆再改比在 2000 行裡改安全。

### Phase C · 研究與擴充（時間視需求，各項獨立）

| 項目 | 內容 | 為什麼值得 | 決策點 |
|---|---|---|---|
| C1 | **學生端作答**：quiz_card 投影時顯示 QR code → 學生手機連校內 LAN 的 `/quiz/{id}` 作答 → 投影機即時長條圖 | Future of Education 最直接的下一步；仍是 on-device（區域網路，不出教室）。技術上只是 FastAPI 多兩條路由 + 一個記憶體 dict。 | 需要教室 Wi-Fi 能讓手機連到老師筆電；很多學校 AP 有 client isolation。先在 NCUT 教室驗證網路再動工。 |
| C2 | **評測集**：`bench/utterances.jsonl`，50–100 句真實課堂逐字稿 + 人工標的模板 → 跑 e2b / e4b / 不同 temperature 的模板命中率、salvage 率、延遲 | 這是論文的實驗段落。現在 history JSON 已有 `_path` / `_salvaged`，資料其實一直在累積。 | CLAUDE.md §9 說「不加測試」是 hackathon 規則。賽後這條要不要解除，由老師決定。建議：解除，但只加 `bench/`，不加 CI。 |
| C3 | **e4b 作為預設**的重新評估 | B1 上線後 ASR 是短段落，可考慮 ASR 降 `medium`（1.5 GB）換 LLM 升 e4b。C2 的數據可以直接回答「e4b 命中率高多少」。 | 等 C2 有數據 |
| C4 | 白板影像（多模態） | WRITEUP §8 的擱置理由（硬體 + VRAM）都還成立 | 除非教室有實物投影機，否則維持擱置 |
| C5 | 操作端自訂 Console（`UI_migration_proposal.md` Pass 2） | 現在 Gradio 操作端功能齊全，老師自己用不需要「好看」 | 只有在要對外發布給其他老師時才值得；排在所有 B 之後 |

### 明確不做

- **雲端 LLM 備援**：on-device 是產品定義，不是實作細節。
- **自由版面**：7 模板夠用；有新需求走「一次一個模板」流程。
- **Docker / CI / mypy**：使用者是 Windows 單機，Ollama 本身就是部署層。
- **React / 建置流程**：`/display` 一個 `<script>` 就夠。

---

## 3. 需要老師決定的事項

| # | 問題 | 建議 | 影響範圍 |
|---|---|---|---|
| Q1 | Hackathon 結果如何？影片連結、截圖要不要放進 README？ | 放。就算沒得獎，「參賽作品」本身是可信度。 | Phase A2 |
| Q2 | Phase B 的順序：先 B1（連續聆聽）還是先 B2（詞彙表）？ | **先 B2 再 B1**。B2 一天可完成、立刻可用；B1 要跑幾堂課調參數。 | 排程 |
| Q3 | 賽後是否解除「不加測試」規則，允許 `bench/`？ | 解除，僅限 `bench/`（評測，不是單元測試），不加 CI。 | C2、論文 |
| Q4 | `no_card` 閘門要不要讓老師在 UI 看到「這段被跳過」？ | 要，操作端顯示灰字一行，投影端不顯示。 | B1 |
| Q5 | Session 目錄命名要不要綁課程名？ | 綁。開始上課時填一次課程名，當天不再問。 | B3 |
| Q6 | C1 學生作答：NCUT 教室 Wi-Fi 手機能否連到筆電？ | 先用手機熱點 + 筆電連熱點測一次，10 分鐘知道答案。 | C1 go / no-go |

---

## 4. 建議的第一週

```
Day 1   A1 文件同步 + A3 釘版本 + A4 .gitignore 確認        （半天）
Day 1   A5 start_sensei.ps1                                    （半天）
Day 2   B2 詞彙表外部化 + 語言下拉                             （1 天）
Day 3   B4 /display 渲染快取 + SSE                             （1 天）
Day 4   B5 app.py 三分法（只搬不改，每步跑 dry_run.ps1）        （1 天）
Day 5   實際上一堂課，用新版跑完整流程，記錄摩擦點             （驗證）
```

第一週結束後，再依 Day 5 的觀察決定 B1 的切句參數與 B3 的 session 設計。

---

## 5. 對 CLAUDE.md 的連動修改（本提案被接受後執行）

- §0 TL;DR：移除「9 天倒數」語氣，改為「v2 目標：老師每週真的在用」。
- §1 現況：更新至賽後狀態。
- §1A：整段移到附錄「Hackathon 歷程（已結束）」，保留「why-not-cloud-LLM」四點，那段仍是產品定義。
- §7 / §8：以本文件 §2、§4 取代。
- §9：「不加測試」改為「不加單元測試與 CI；`bench/` 評測集允許」（若 Q3 同意）。
- §3 關鍵決策表：新增一列「連續聆聽的 `no_card` 閘門 — 不要拿掉，否則投影機每句話都閃」。

---

*Sensei · 先生 — 賽後的目標只有一個：下週的課，老師會不會打開它。*
