# Sensei · 課程詞彙表（ASR glossary）

每個 `.txt` 是一份 Whisper `initial_prompt`：一段描述課程情境 + 常見專有名詞的短文。
Whisper 會把它當成「這段音訊大概會出現哪些詞」的軟性先驗，對中英夾雜的工程術語
（PID、SCADA、Modbus…）辨識率提升約 40–60 %。

## 檔名規則

```
<id>.<lang>.txt        例：auto_control.zh.txt、general.en.txt
```

- `<id>`：英文小寫 + 底線，出現在操作端下拉選單的值
- `<lang>`：`zh` 或 `en`，決定 Whisper 的 `language` 參數（`auto` 由操作端另外選）
- 以 `_` 開頭的檔案不會出現在選單（例：`_template.txt`）

## 檔案格式

```
# title: 自動控制（繁中）          ← 第一行：下拉選單顯示名稱
# 任何以 # 開頭的行都是註解，不會送進 Whisper
本逐字稿是……課程的講課內容。可能出現的專有名詞：
PID 控制、比例積分微分、……
```

非註解的行會以空白串接後整段送進 Whisper。**總長建議 ≤ 200 字**：Whisper 的
prompt 上限是 224 tokens，超過的部分會被截掉（從頭截，留尾巴），所以把最重要的
詞放在最後。

## 新增一門課

1. 複製 `_template.txt` 為 `<你的課>.zh.txt`
2. 改第一行 `# title:`，填入該課的專有名詞
3. 重新啟動 Sensei，操作端「課程詞彙表」下拉就會出現

不需要改任何 Python 程式碼。歡迎用 PR 分享你的詞彙表（見 CONTRIBUTING.md）。
