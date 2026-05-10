# Sensei · Demo 影片腳本 (3 分鐘) — 混合拍法版

> 目標觀眾：Kaggle Gemma 4 Good Hackathon 評審（英語為主、需要中文字幕）。
> 核心訊息：「On-device AI co-teacher. No cloud. Runs on a laptop.」
> 影片總長：≤ 3 分鐘（YouTube unlisted）。
>
> **拍法**：相機（拍人 + 環境）＋ 螢幕錄影（拍 UI 內容），剪接時混搭。
> 不用相機硬拍螢幕（會有摩爾紋、反光、模糊），所有 UI 畫面用螢幕錄影 → pixel-perfect。

---

## 0. 兩條獨立軌道

拍攝時**同時錄三個來源**，剪接時挑、切、混：

| 軌 | 來源 | 內容 |
|---|---|---|
| **A. 相機** | 手機 / 攝影機 + 三腳架 | 老師臉部、手勢、走位、教室全景、指投影機的動作 |
| **B. 螢幕錄影 — `/display`** | OBS / Game Bar 錄外接螢幕 | 投影機那面看到的卡片內容（pixel-perfect） |
| **C. 螢幕錄影 — Operator** | OBS 錄筆電主畫面 | Sensei 操作介面、F8 觸發、按鈕點擊特寫 |

**麥克風**：用外接麥（避免筆電風扇 / 鍵盤聲），講話時對準老師。三軌都用同一個外接麥的音軌做時間對齊。

---

## 1. 時間軸總覽（每段標明用哪一軌）

| 段 | 時間 | 內容 | 主要鏡頭 |
|---|---|---|---|
| §1 | 0:00–0:20 | Cold open · 課堂痛點 | A（老師背影 / 學生 / 黑板靜止鏡頭） |
| §2 | 0:20–0:45 | Sensei 是什麼 | A 老師臉特寫 + B `/display` 第一張卡淡入 |
| §3 | 0:45–2:15 | **Live demo（核心）** | A + B + C 三軌切換 |
| §4 | 2:15–2:45 | Why Gemma 4 / Ollama | 文字 overlay + B 卡片背景 |
| §5 | 2:45–3:00 | Outro · Repo & License | 文字卡 |

---

## 2. §1 Cold open（0:00–0:20）

**[軌 A 相機]** 教室場景。老師手勢豐富在黑板前講話。學生坐著看著黑板上的「Lesson 5: Control Methods」 — 一個靜態、無聊的標題。鏡頭停在黑板上 5 秒，再切到老師嘴在動的特寫。

**Voiceover（中、英文字幕）**：

> 每個課堂都有這個落差 — 老師講出豐富、有結構的內容，學生看到的是靜止的投影片。
> Every classroom has the same gap: teachers speak rich, structured ideas — students see static slides.

**[後製疊加文字 3 秒]**：

```
The structure is in the teacher's head, not on the screen.
```

---

## 3. §2 Sensei intro（0:20–0:45）

**[後製] 0:20–0:25** — 黑底，Sensei 標誌淡入。Tagline 浮現。

**[軌 A 0:25–0:35]** — 老師走近電腦、手準備按 F8（不要實際按 — 是「準備好」的視覺暗示）。

**[軌 B 0:35–0:45]** — 切到 `/display` 螢幕錄影：第一張卡片淡入，paper editorial 風格。畫面停留約 5 秒讓觀眾看清。

**Voiceover**：

> 這是 Sensei — 課堂 AI 副教師。聽老師講話，即時把內容變成結構化視覺卡片。
> 不上雲端、不漏音訊、跑在一台筆電上。
>
> Meet Sensei. An on-device AI co-teacher. No cloud. No privacy risk. Runs on a single laptop.

---

## 4. §3 Live demo（0:45–2:15） — 核心 90 秒

**設置（拍攝時）**：
- Sensei 跑在筆電上，主介面在筆電螢幕（**OBS 同時錄筆電 + 外接螢幕兩軌**）
- 投影機顯示 `/display`，paper 主題、F11 全螢幕
- 老師站在投影機前 2-3 公尺，手裡有滑鼠或筆電鍵盤可按
- 相機架三腳架，拍老師中近景（含半身 + 投影機在背景）

### Demo A — Enumeration（0:45–1:15，30 秒）

**[軌 A 0:45–0:50]** — 老師面對鏡頭，講第一句：

> 「同學，控制方法不只有 PID 控制，其實還有最佳控制、類神經控制、非線性控制、強健控制。」

老師按 F8 開始錄音（手指接近鍵盤的特寫可以後製插）

**[軌 C 0:50–0:55]** — 切到操作介面螢幕錄影 zoom-in，看到「⏹ 停止並生成 (F8)」按鈕，右上角狀態列顯示「🔴 錄音中…」

**[軌 A 0:55–1:05]** — 切回老師臉部，講話節奏接著：

> 「這些是 PID 之外可以用的進階控制策略。」

老師再按 F8 結束（特寫滑鼠 / 鍵盤）

**[軌 B 1:05–1:15]** — 切到 `/display` 螢幕錄影 zoom-in：5 張卡片以淡入動畫依序出現，每張有 icon + 名稱 + 短副標。停留約 8 秒讓觀眾讀完。

**字幕（英文，從 0:45 持續）**：
> "Control isn't only PID — there's also optimal, neural, nonlinear, robust control."

### Demo B — Extend（1:15–1:45，30 秒） · 殺手功能

**[軌 A 1:15–1:25]** — 老師指著投影機畫面（背景模糊看得到 5 張卡），補充：

> 「對，剛剛漏了，還可以加上**自適應控制**跟**增益調節控制**這兩個。」

**[軌 C 1:25–1:30]** — 切到操作介面螢幕錄影特寫：滑鼠移到「延伸上一張」按鈕、點擊。

**[軌 B 1:30–1:45]** — 切到 `/display`：原本 5 張卡 → 變成 7 張，新加的兩張用淡入動畫帶出（顏色稍微不同，用視覺暗示「新項目」）。停留約 12 秒。

**字幕**：
> "Oh — also adaptive control and gain scheduling. **Click 'Extend.'**"
>
> *The card grows in place. Original 5 stay, 2 new ones added.*

### Demo C — Flow diagram（1:45–2:15，30 秒）

**[軌 A 1:45–1:55]** — 老師轉換主題：

> 「以風機監控系統來看，整個流程是這樣 — 我們先量測振動、再做特徵抽取、接著分類診斷、最後產生告警。」

按 F8 開始 → 講完 → 按 F8 結束。

**[軌 B 1:55–2:15]** — 切到 `/display`：流程圖卡片淡入，4 步驟橫向排列、有大箭頭（paper editorial 風格）。停留約 18 秒。

**字幕**：
> "Wind turbine monitoring: measure → extract → classify → alert."

---

## 5. §4 Why this works（2:15–2:45，30 秒）

**[後製] 黑底 + 三個重點文字框漸進浮現** — **不需要拍片**，純後製。

**Voiceover**：

> 為什麼這樣設計？三個關鍵：
>
> 一、Gemma 4 不是被當「百科」用，是被當「結構化引擎」用。所以 e2b 小模型就夠 — 整套才能跑在筆電上。
>
> 二、結構化輸出有三道保險 — Gemma 4 原生工具呼叫、Ollama JSON mode、Pydantic schema 驗證。
>
> 三、沒有任何音訊離開教室。沒有訂閱費。沒有網路也能跑。
>
> Sensei is a *structuring engine*, not an oracle. Three layers of reliability. Nothing leaves the room.

**疊加文字（依序）**：
```
1.  Structuring engine, not oracle  →  small model is enough
2.  Tool calling + JSON mode + Pydantic  →  three-layer safety
3.  No cloud, no bills, no network dependency  →  works in any classroom
```

---

## 6. §5 Outro（2:45–3:00，15 秒）

**Visual**：黑底，Sensei logo 中央。下方文字：

```
github.com/dofliu/sensei
CC-BY 4.0  ·  built for Gemma 4 Good Hackathon
Made by Dof Lab · NCUT

Try it. Share it. Teach with it.
```

**Voiceover**：

> Sensei — 給每位老師、在任何地方，都能擁有一位副教師。
>
> Sensei. So any teacher, anywhere, can have a co-teacher.

---

## 7. 拍攝設置（重新整理 — 取代舊版）

### 三軌同時錄影設置

| 軌 | 工具 | 設定 |
|---|---|---|
| A. 相機 | 手機 1080p 60fps + 三腳架 | 中近景、固定機位、不必移動 |
| B. /display 螢幕錄 | OBS Studio · 「外接顯示器」來源 | 1080p 60fps、不錄音 |
| C. Operator 螢幕錄 | OBS 同檔多軌 / 第二個 OBS 設定檔 | 1080p 60fps、不錄音 |
| 麥克風 | USB 外接麥 / 動圈麥 → 接筆電 | 三軌同時收這支麥的音 → 後製對齊 |

**OBS 多場景設置（推薦）**：
- 場景 1：「Camera」（只有相機）
- 場景 2：「Display recording」（外接螢幕）
- 場景 3：「Operator recording」（筆電螢幕）
- 三場景**同時錄影**用 OBS 的 Replay Buffer 功能，或同一個 session 三軌分別錄

### 後製剪接

- 軟體：DaVinci Resolve（免費）/ Capcut Desktop（免費，更簡單）
- 對齊：用麥克風那條共同音軌對齊三軌畫面
- 切換頻率：平均每 5-10 秒切一次鏡頭，不要長時間停在同一畫面（觀眾分心）
- 字幕：中英雙語、底部置中、留白 10% 視窗高度
- 字體：英文用 Instrument Serif（標題）/ Geist（內文）— 跟 Sensei UI 一致

### Demo 軸對齊小技巧

老師講話時的時間軸：
1. 軌 A 拍老師的「動作」 — 開口、按鍵、指畫面
2. 軌 C 在「按鍵那一秒」應該對應 UI 上的點擊
3. 軌 B 在「卡片應該出現那一秒」應該有淡入動畫

剪接時：A 鏡頭起 → C 點擊瞬間切到 → 1-2 秒後切到 B 看結果 → 切回 A 老師反應。

這個 A→C→B→A 循環是 demo 影片的「節拍器」，所有 demo 段照這個節奏剪。

---

## 8. 後製清單（取代舊版）

- [ ] 中英雙字幕（英文為主）
- [ ] 開頭 0.5 秒淡入、結尾 0.5 秒淡出
- [ ] 三軌時間軸對齊（用麥克風音軌）
- [ ] B 軌（/display）每次出現可加細邊框或 zoom-in 動畫，幫助觀眾辨識
- [ ] C 軌（operator）UI 操作可加滑鼠軌跡 / 點擊閃光（DaVinci 有內建）
- [ ] 背景音樂可選：低音量 lo-fi / 純鋼琴，-25 dB，§3 期間音量壓更低
- [ ] 上傳 YouTube unlisted、1080p 或更高
- [ ] 連結加到 Kaggle 提交表單

---

## 9. 緊急狀況備案

| 情境 | 怎麼辦 |
|---|---|
| 三軌同時錄太麻煩 | 退到「相機 + 螢幕錄外接螢幕」兩軌；§3 的 operator 鏡頭省略，改用文字 overlay 解釋「老師按 F8 觸發」 |
| 投影機畫面相機看起來糊 | 那段就純用螢幕錄影、不用相機；老師臉的鏡頭單獨補拍 |
| F8 在拍攝時無反應 | 改用紅色大按鈕，剪接時把鍵盤鏡頭換成滑鼠鏡頭 |
| Sensei 卡住 / 出錯 | 留 history JSON，重啟後從上次斷點繼續；剪接時跳過當機段 |
| 時間真的拍不完 | 砍 Demo C（flow diagram）— 留 A + B 兩段就夠講完整故事 |
