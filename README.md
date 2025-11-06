# StarRail Discord 6 Bot

一個簡單的 Discord Bot，會在每週固定時間提醒大家、回覆幾個關鍵字，並提供狀態檢查指令。

**功能**
- 每週日 09:00（Asia/Taipei）在指定頻道發送提醒訊息。
- 關鍵字互動：
  - 傳「六」→ 回覆「真是太6了」並加上 6️⃣ 反應。
  - 傳「真是太6了」或「真是太六了」→ 回覆「6」並加上 6️⃣ 反應。
  - 傳「6...」→ 回覆 6 的 ASCII 圖。
  - 傳「3/7」→ 回覆一張 GIF 圖連結。
- 狀態檢查指令：`!status` / `!狀態` / `!状态` / `!st`
  - 顯示 Scheduler 狀態、目標頻道、是否具備發訊權限、下一次排程時間與現在時間。
- 監控成員狀態/遊戲：若有人狀態或遊戲包含關鍵字（預設含「Honkai」「星鐵」「星穹」等），在指定頻道 @ 他提醒去讀書（含冷卻避免洗頻）。

---

**需求**
- Python 3.9+（建議 3.10 以上）
- Discord Bot Token
- 已啟用 Privileged Gateway Intents：
  - Message Content Intent（訊息內容）
  - Presence Intent（線上狀態）
  - Members Intent（成員）

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
  - Bot 也會在這個頻道提醒「去讀書」。
- `PRESENCE_KEYWORDS`（可選）：狀態/遊戲監看關鍵字；以分號 `;` 分隔。
  - 預設：`honkai;star rail;崩壞;崩坏;崩壊;星穹;星鐵;星铁`
- `PRESENCE_COOLDOWN_MIN`（可選）：對同一人提醒的冷卻分鐘數，預設 `120`。

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

---

**指令**
- `!status` / `!狀態` / `!状态` / `!st`
  - 顯示：
    - Bot 帳號
    - Scheduler 狀態（Running/Paused/Stopped）
    - 目標頻道、是否具備發訊權限
    - 下一次排程時間
    - 現在時間（UTC）
  
Bot 也會被動監聽成員狀態/遊戲變更（需 Presence/Members Intents）。當由「不含關鍵字」變成「含關鍵字」時，會在 `CHANNEL_ID` 指定頻道 @ 當事人提醒去讀書。具備冷卻機制避免洗頻，可用 `PRESENCE_COOLDOWN_MIN` 調整。

---

**權限與設定注意事項**
- Bot 必須在目標伺服器中，且對 `CHANNEL_ID` 指定頻道擁有「發送訊息」權限。
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
