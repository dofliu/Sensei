# Day 7 拍攝 Day Checklist

> 給你拍攝當天逐項對照用。最遲拍攝前一晚把所有 ❗ 項目跑過一遍。

## ❗ 拍攝前 24 小時必確認

- [ ] **先跑自動 preflight**：`cd D:\Project_CodingSimulation\PersonalHelper\sensei` → `.\dry_run.ps1`。9 條檢查（env vars / Whisper cache / Ollama / Python deps / 音訊裝置 / LLM 分類 / quiz 語音觸發 …）全綠才往下走。出現 FAIL 一律先修；列出來的 hint 行通常就是修法。約 35 秒。
- [ ] Sensei 重啟一次後完整跑通 7 種模板的範例（enumeration / comparison / flow / hierarchy / SWOT / pyramid / quiz_card）
- [ ] 對著麥克風講「來考一題，下列哪個是…」確認 quiz_card 語音觸發在實際 ASR + pipeline 下會生效（substring 命中印 `[Pipeline] quiz trigger phrase detected`）
- [ ] `/display` F11 全螢幕在外接螢幕上正常顯示、卡片淡入動畫流暢
- [ ] F8 / Ctrl+Space 都能觸發錄音
- [ ] 主題切換 dark / light / paper 都正常
- [ ] 麥克風裝置正確（Windows 聲音設定 → 輸入裝置選對的）
- [ ] 試錄一段：講 30 秒 → 看逐字稿是否準確、`_path` 是否合理

## 硬體

- [ ] **主筆電**（RTX 4080）— 充電 100%、電源插好（4 小時拍攝過程不能斷電）
- [ ] **外接螢幕 / 投影機**（投 `/display`）— HDMI / USB-C 線接好
- [ ] **外接麥克風**（**強烈建議**）— 筆電內建麥克風會收到鍵盤、風扇雜音；用 USB / 3.5mm 麥就能大幅改善
- [ ] **耳機**（事後試聽錄音）
- [ ] **拍攝相機**：手機（iPhone 14+ / 任何旗艦 Android）足夠 → 1080p 60fps
- [ ] **三腳架**（拍人像穩定性 critical；手持會晃）
- [ ] **補光燈**（如果室內偏暗；窗邊自然光 + 一盞檯燈也可）

## 軟體環境

- [ ] Sensei 已啟動：`python -m frontend.app`
- [ ] 主操作介面開在筆電上，預設 Live 分頁
- [ ] `/display` 開在外接螢幕、F11 全螢幕、主題 = dark
- [ ] **歷史紀錄清空**（`history/` 目錄移走或新建乾淨環境）— 拍攝時不希望舊卡片混進去
- [ ] **螢幕錄製軟體**：OBS Studio（免費，建議）/ Windows Game Bar（Win+G）/ macOS QuickTime
  - OBS 設定：1080p 60fps、來源加「外接螢幕」+「老師臉部 webcam」+「麥克風音訊」
- [ ] **影片剪輯軟體**：DaVinci Resolve（免費）/ Capcut Desktop（免費）/ Premiere（付費）
  - 至少要能：剪片頭片尾、加字幕、調聲音音量

## 場地與聲音

- [ ] **安靜空間**：拍攝時段確認沒有其他人會進來
- [ ] **關冷氣 / 風扇**（如果有風聲就毀了）
- [ ] **手機調靜音**（自己的、現場其他人的）
- [ ] **電腦通知關掉**（Windows 焦點輔助 / Slack / 信件）
- [ ] **避免回音空間**：地毯 / 沙發 / 窗簾多的房間最好；空辦公室回音會很差

## 拍攝流程（建議 60–90 分鐘）

### 第 1 階段：技術空跑（15 分鐘）
1. 不開錄影，照 [DEMO_SCRIPT.md](./DEMO_SCRIPT.md) 從頭演練一次
2. 測時間：每段是不是落在預估時間
3. 找出可能卡住的地方（F8 沒按到、講錯字、卡片沒出來）

### 第 2 階段：正式拍攝（30 分鐘）
1. 開螢幕錄影 + 麥克風 + 攝影機（三軌同時）
2. 從 §3 開始拍（demo 是核心；§1、§2、§4、§5 主要是 voiceover + overlay，可以後製）
3. **每段拍 2–3 take**，不要一次過。剪接時挑最好的
4. NG 不要重來整段，繼續講下一句，剪接時切掉

### 第 3 階段：補拍（15 分鐘）
1. 整段重看，找需要補拍的地方
2. 拍特寫：滑鼠點按鈕、F8 按鍵特寫、`/display` 卡片淡入近拍

### 第 4 階段：後製初稿（30 分鐘）
1. 三軌素材匯入剪輯軟體
2. 對齊聲音時間軸
3. 切粗剪：去掉 NG、過長停頓
4. 加開頭 / 結尾畫面、字幕

## 字幕

- 中文 + 英文雙語顯示（評審以英語為主）
- 字體：Noto Sans TC / 思源黑體 / 黑體
- 大小：60+ pt 給 1080p
- 位置：底部居中，留白 10% 視窗高度
- 重點英文（demo 對白）建議手動逐句翻譯，不要 YouTube 自動翻譯

## 上傳與提交

- [ ] YouTube 上傳：**Unlisted（不公開但有連結可看）**
- [ ] 標題：`Sensei · On-Device AI Co-Teacher | Gemma 4 Good Hackathon Submission`
- [ ] 簡介：放專案連結 + 一段話 problem statement + 投稿 track
- [ ] 把連結貼到 Kaggle 提交表單

## 緊急狀況備案

| 情境 | 怎麼辦 |
|---|---|
| Sensei 啟動失敗 | 重灌 `pip install -r requirements.txt`；確認 Ollama 在跑 |
| Whisper 認不出某個專有名詞 | 編輯 `core/asr.py::ASRConfig.INITIAL_PROMPT` 加上那個詞、重啟 |
| `/display` 沒更新 | 重新整理瀏覽器（Ctrl+Shift+R） |
| F8 沒反應 | 改用畫面上的紅色大按鈕，剪接時把鍵盤特寫換成滑鼠特寫 |
| 拍到一半當機 | 留下 history JSON 檔，重啟後從上次斷點繼續；剪接時跳過當機那一刻 |
| 時間真的拍不完 | 縮短 §3 的 demo C（hierarchy）— 留 A + B 兩段就夠秀完整故事 |
