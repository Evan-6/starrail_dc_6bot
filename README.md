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
- `NEW/commands/` — Feature cogs: `status`, `say`, `gemini_cmd` (jemini), `sixstats`, `codes`, `analyze`.
- `NEW/utils/` — Small helpers and constants.

Notes
- Slash commands are synced on startup. Set `GUILD_ID` for faster per-guild sync during development; unset for global sync.
- Scheduler runs a weekly reminder on Sundays at 09:00 (`TIMEZONE` default `Asia/Taipei`).
- Presence monitor is modularized; enable by setting `PRESENCE_ENABLED=true`.

