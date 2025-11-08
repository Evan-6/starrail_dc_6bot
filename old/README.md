# StarRail Discord 6 Bot

Note: A modular refactor is available under `NEW/`. The original `main.py` remains unchanged. To run the refactor: `python -m NEW.app`.

一個簡單的 Discord Bot，會在每週固定時間提醒大家、回覆幾個關鍵字，並提供狀態檢查指令。

**功能**
- 每週日 09:00（Asia/Taipei）在指定頻道發送提醒訊息。
- 關鍵字互動：
  - 傳「六」→ 回覆「真是太6了」並加上 6️⃣ 反應。
  - 傳「真是太6了」或「真是太六了」→ 回覆「6」並加上 6️⃣ 反應。
  - 傳「6...」→ 回覆 6 的 ASCII 圖。
  - 傳「3/7」→ 回覆一張 GIF 圖連結。
- 狀態檢查：`!status` 與 `/status`
  - 顯示 Scheduler 狀態、下一次排程時間與現在時間。
- 監控成員狀態/遊戲（目前預設關閉，程式碼已註解）：
  - 若啟用，可在指定頻道提醒去讀書（含冷卻避免洗頻）。
- Slash 指令：
  - `/status`：以 ephemeral 回覆狀態資訊。
  - `/sixstats`：統計本頻道過去 N 天（預設 7 天）每位使用者含有「6/六」的訊息數（每則訊息最多算一次），可選擇僅自己可見。
  - `/say`：讓 Bot 發一段文字。
  - `/jemini`：使用 Google Gemini 生成文字（需設定 API Key；回覆限制 1900 字內）。
  - `/codes`：使用 Gemini 檢查過去 N 天全伺服器的「兌換碼」訊息並整理為表格（回覆限制 1900 字內），可選擇僅自己可見。
  - `/analyze`：讀取本頻道過去 N 天的訊息，套用你提供的指令交給 Gemini 進行自訂分析（回覆限制 1900 字內），可選擇僅自己可見。

---

**需求**
- Python 3.9+（建議 3.10 以上）
- Discord Bot Token
- 已啟用 Privileged Gateway Intents：
  - Message Content Intent（訊息內容）
  - Presence Intent（線上狀態）
  - Members Intent（成員）
 - OAuth2 邀請需包含 `applications.commands` 與 `bot` scope。

在 Discord 開發者後台：Bot → Privileged Gateway Intents → 勾選「MESSAGE CONTENT」「PRESENCE」「SERVER MEMBERS」。

---

**安裝**
1. 下載此專案程式碼。
2. 安裝相依套件：
   - Windows PowerShell
     - 建議先建立虛擬環境：
       - `python -m venv .venv`
       - `.\.venv\Scripts\Activate.ps1`
     - 安裝需求：
       - `pip install -r requirements.txt`
   - macOS/Linux
     - `python3 -m venv .venv && source .venv/bin/activate`
     - `pip install -r requirements.txt`

---

**環境變數**
- `DISCORD_TOKEN`：你的 Bot Token。
- `CHANNEL_ID`：要發送排程提醒訊息的文字頻道 ID（整數）。
  - 若啟用狀態監控，亦會在此頻道提醒「去讀書」。
- `PRESENCE_KEYWORDS`（可選）：狀態/遊戲監看關鍵字；以分號 `;` 分隔。
  - 預設：`honkai;star rail;崩壞;崩坏;崩壊;星穹;星鐵;星铁`
- `PRESENCE_COOLDOWN_MIN`（可選）：對同一人提醒的冷卻分鐘數，預設 `120`。
- `GUILD_ID`（可選）：開發/測試伺服器的 ID。若設定，Slash 指令會只同步到該伺服器，立即生效；未設定則做全域同步（可能需數分鐘）。
- `GEMINI_API_KEY`（可選）：使用 `/jemini` 指令所需的 Google Gemini API Key。

設定方式範例：
- Windows PowerShell
  - `$env:DISCORD_TOKEN = "你的Token"`
  - `$env:CHANNEL_ID = "123456789012345678"`
- macOS/Linux（Bash/Zsh）
  - `export DISCORD_TOKEN="你的Token"`
  - `export CHANNEL_ID=123456789012345678`

---

**執行**
- Windows：`python .\main.py`
- macOS/Linux：`python3 main.py`

Bot 啟動後不會自動發送訊息，僅會在排程時間觸發（每週日 09:00 Asia/Taipei）。
首次啟動會同步 Slash 指令：
- 若設 `GUILD_ID` → 立即可用。
- 若無 → 進行全域同步，可能需數分鐘才會在用戶端顯示。

---

**指令**
- `!status`
  - 顯示：Scheduler 狀態（Running/Paused/Stopped）、下一次排程時間、現在時間（UTC）。

Slash 指令：
- `/status`：以 ephemeral 顯示狀態資訊。
- `/sixstats [days] [private]`：統計本頻道過去 `days` 天（1–30，預設 7）每位使用者含有「6/六」的訊息數（每則訊息最多算一次）。`private` 預設為 True。
- `/say text`：讓 Bot 發送 `text`。
- `/jemini prompt`：用 Gemini 生成回覆（需 `GEMINI_API_KEY`；回覆限制 1900 字內）。
- `/codes [days] [private]`：使用 Gemini 檢查過去 `days` 天（1–30，預設 7）全伺服器可讀取的訊息，彙整包含「兌換碼/兑换码/序號」等關鍵字或疑似代碼的訊息為表格（回覆限制 1900 字內）。`private` 預設為 True。
 - `/analyze instruction [days] [private]`：讀取本頻道過去 `days` 天（1–30，預設 7）的訊息，將這些訊息作為上下文交給 Gemini，依你的 `instruction` 進行自訂分析（回覆限制 1900 字內）。`private` 預設為 True。

---

**權限與設定注意事項**
- Bot 必須在目標伺服器中，且對 `CHANNEL_ID` 指定頻道擁有「發送訊息」權限。
- `/sixstats` 需要在目標頻道具備「讀取訊息歷史」與「讀取訊息」權限。
- `/codes` 需要在伺服器各文字頻道具備「讀取訊息」與「讀取訊息歷史」權限，且使用 Gemini 會消耗 API 配額。
 - 所有使用 Gemini 的回覆都會限制在 1900 字元以內，以避免超過 Discord 單則訊息 2000 字元上限。
- 若 `!status` 顯示找不到頻道或沒有發訊權限，請檢查：
  - 邀請範圍與權限是否足夠（Send Messages）。
  - `CHANNEL_ID` 是否正確（右鍵頻道 → 複製 ID，需要開啟「開發者模式」）。
  - 是否已啟用 Intents 並在程式中設定：
    - `intents.message_content = True`
    - `intents.members = True`
    - `intents.presences = True`

---

**排程**
- 使用 APScheduler 的 BackgroundScheduler。
- 預設排程：每週日 09:00（Asia/Taipei）在 `CHANNEL_ID` 指定的文字頻道發送：
  - `@here 記得打模擬宇宙ʕ•̫͡•ʔ•̫͡•ʔ•̫͡•ʕ•̫͡•ʔ•̫͡•ʔ`
- 可在 `main.py` 中調整 `@scheduler.scheduled_job(...)` 的 `day_of_week/hour/minute/timezone`。

---

**疑難排解**
- 啟動後毫無反應：
  - 檢查 `DISCORD_TOKEN` 是否正確、Bot 是否已加入伺服器。
  - 在任一文字頻道輸入 `!status` 檢查權限與排程狀態。
- 看不到回覆/排程訊息：
  - 確認 Bot 在該頻道擁有發送訊息權限。
  - 確認 `CHANNEL_ID` 正確。
  - 確認 Message Content Intent 已啟用。
