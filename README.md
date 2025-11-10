New modular structure for the Discord bot. The original `main.py` remains untouched.

How to run
- Set required environment variables: `DISCORD_TOKEN`, `CHANNEL_ID`, `GEMINI_API_KEY`.
- Optional: `GUILD_ID`, `PRESENCE_ENABLED`, `PRESENCE_KEYWORDS`, `PRESENCE_COOLDOWN_MIN`, `TIMEZONE`.
- Start the refactored bot: `python -m NEW.app`

Structure
- `NEW/app.py` — Entry point; loads cogs, events, and runs the bot.
- `NEW/config.py` — Environment-driven configuration.
- `NEW/bot/client.py` — Creates the `commands.Bot` with intents.
- `NEW/bot/events.py` — Core events: `on_ready`, `on_message`.
- `NEW/bot/scheduler.py` — APScheduler instance, jobs, and status helper.
- `NEW/bot/presence.py` — Optional presence monitor (gated by `PRESENCE_ENABLED`).
- `NEW/services/gemini_service.py` — Gemini text generation service.
- `NEW/commands/` — Feature cogs: `status`, `say`, `gemini_cmd` (jemini, vision),
  `context_menus` (Summarize/Reply/Moderate), `summarize`, `language` (translate/polish),
  `askdoc`, `digest`, `topics` (analyze_topics), `moderate`, `chat`, `sixstats`, `codes`, `analyze`.
- `NEW/utils/` — Small helpers and constants.
- `NEW/data/schedules.json` ?? JSON reminder definitions (auto-created if missing).

Notes
- Slash commands are synced on startup. Set `GUILD_ID` for faster per-guild sync during development; unset for global sync.
- Scheduler reminders are backed by `NEW/data/schedules.json`; manage them via `/schedule`.
- Default reminder fires on Sundays at 09:00 (`TIMEZONE` default `Asia/Taipei`).
- Presence monitor is modularized; enable by setting `PRESENCE_ENABLED=true`.

Commands (highlights)
- `/jemini prompt:<text>` — Gemini text generation with output trimmed to 1900 chars.
- `/vision prompt:<text> image:<attachment> [private:true]` — Gemini Vision: upload an image and ask a question.
- Context menus (message right click): Summarize with Gemini, Reply with Gemini, Moderate Message.
- `/summarize [days|count] [private]` — Summarize channel messages.
- `/translate text:<content> to:<lang>` — Translate text.
- `/polish text:<content> [tone]` — Polish writing tone and clarity.
- `/askdoc question:<text> [use_pins|days] [private]` — Q&A from pins or recent messages.
- `/digest period:<daily|weekly> [private]` — Produce channel digest.
- `/analyze_topics [days] [private]` — Topic clustering, keywords, sentiment.
- `/moderate text:<content> [private]` — Classify content risks.
- `/chat start|status|stop|say` — Lightweight multi-turn chat with short memory per channel.
- `/status` — Check scheduler status and next run time.
- `/schedule list|create|update|delete|run` ?? Manage reminders (mutating commands require Manage Server).
- `/sixstats [days] [private]` — Count messages containing 6/六 in the channel.
- `/codes [days] [private]` — Aggregate potential redeem codes across channels, summarized by Gemini.
- `/analyze instruction:<text> [days] [private]` — Custom channel analysis summarized by Gemini.
