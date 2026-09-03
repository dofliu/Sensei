# Sensei · 專案介紹影片

3 分鐘完整版介紹影片的原始素材。成品:`sensei_intro.mp4`(1920×1080 / 30 fps / 約 2:59)。

由 `repo-intro-video` skill 產出:22 個 standalone HTML 場景 → 無頭瀏覽器逐格渲染 →
ffmpeg xfade 轉場串接 + 安靜合成氛圍配樂。

## 檔案

```
promo/
├── build_scenes.py       ← 22 景的內容與版面都在這裡（唯一要改的檔案）
├── storyboard.json       ← 由 build_scenes.py 產生：每景檔名 / 秒數 / 轉場
├── scene01_hook.html …   ← 由 build_scenes.py 產生的 standalone 場景（22 個）
├── work/                 ← 渲染中間檔：每景 .mp4 + check_*.png 抽查格
└── sensei_intro.mp4      ← 成品
```

`work/` 與 `*.html` 都是產生物,可以安全刪掉重建。

## 影片結構

| 章 | 景 | 色調 |
|---|---|---|
| 開場 | 1 hook · 2 問題 · 3 定位 | teal / violet |
| 管線 | 4 一鏡到底 · 5 ASR · 6 tool calling · 7 四層防線 | teal |
| 模板 | 8 七模板 · 9 列舉 · 10 比較表 · 11 流程圖 | 暖琥珀 |
| 課堂 | 12 語音觸發 · 13 quiz 投影 · 14 SSE 推播 · 15 多語主題 | 黑板綠 |
| 戲劇 | 16 沒有雲端 · 17 四個理由 | 高對比（全片唯一的 fadeblack 切入） |
| 成果 | 18 數據 · 19 課後 · 20 詞彙表 · 21 開源 | violet |
| CTA | 22 repo + 署名 | teal / violet |

## 怎麼改

### 改一句文案

1. 在 `build_scenes.py` 找到那一景的 `scene(...)` 區塊,改 `body` 裡的字。
2. 重新產生 HTML 並只重渲該景:

```powershell
$skill = "<repo-intro-video skill 路徑>"
python build_scenes.py
python "$skill\scripts\render_scenes.py" storyboard.json --workdir work --only scene09_enum
```

3. 看 `work/check_scene09_enum.png` 確認排版,再重新合成(秒級):

```powershell
python "$skill\scripts\assemble_video.py" storyboard.json --workdir work --out sensei_intro.mp4 --bed
```

### 改長度

改 `scene(...)` 的秒數參數。總長 = 各景秒數總和 − (景數−1) × 0.6。
`build_scenes.py` 跑完會直接印出算好的總長。**單景不要超過 10 秒**,節奏靠換景不靠拉長。

### 換配樂

只要重跑 assemble,不用重渲:

```powershell
# 換成自己的音樂檔（比片長短會自動交叉淡接循環，尾 3 秒淡出）
python "$skill\scripts\assemble_video.py" storyboard.json --workdir work --out sensei_intro.mp4 --music bgm.mp3

# 想更小聲（預設 -16 LUFS）
python "$skill\scripts\assemble_video.py" storyboard.json --workdir work --out sensei_intro.mp4 --music bgm.mp3 --loudness -20

# 完全無聲（要自己後製旁白時用這個）
python "$skill\scripts\assemble_video.py" storyboard.json --workdir work --out sensei_intro.mp4
```

目前成品用的是 `--bed`(安靜合成氛圍,-23 LUFS),音量刻意壓低,直接疊旁白也不會打架。

## 加旁白

影片節奏是照「唸得完」排的,每景 7–10 秒。要配旁白的話,
`build_scenes.py` 裡每一景的文案就是現成的旁白稿骨架,在剪輯軟體裡疊上去即可。

## 環境需求

- Python + `playwright`(瀏覽器用系統既有的 Chromium,**不要**跑 `playwright install`)
- `ffmpeg`(需要 xfade / libx264 / aac)
- Noto Sans CJK TC 字型(繁中字卡)

Chromium 版本與 playwright 對不上時,設 `CHROMIUM_PATH` 指向瀏覽器執行檔。
