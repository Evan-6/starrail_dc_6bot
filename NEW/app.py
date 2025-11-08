import asyncio
import importlib

from NEW import config
from NEW.bot.client import create_bot
from NEW.bot.events import setup_events


async def _load_cogs(bot):
    # Commands cogs
    for mod in [
        "NEW.commands.status",
        "NEW.commands.say",
        "NEW.commands.gemini_cmd",
        "NEW.commands.context_menus",
        "NEW.commands.summarize",
        "NEW.commands.language",
        "NEW.commands.askdoc",
        "NEW.commands.digest",
        "NEW.commands.topics",
        "NEW.commands.moderate",
        "NEW.commands.chat",
        "NEW.commands.sixstats",
        "NEW.commands.codes",
        "NEW.commands.analyze",
    ]:
        m = importlib.import_module(mod)
        if hasattr(m, "setup"):
            await m.setup(bot)

    # Optional presence monitor
    if config.PRESENCE_ENABLED:
        m = importlib.import_module("NEW.bot.presence")
        if hasattr(m, "setup"):
            await m.setup(bot)


def main():
    bot = create_bot()
    setup_events(bot)

    @bot.event
    async def setup_hook():
        await _load_cogs(bot)

    token = config.DISCORD_TOKEN
    if not token:
        raise RuntimeError("DISCORD_TOKEN 未設定。請先設定環境變數 DISCORD_TOKEN。")
    bot.run(token)


if __name__ == "__main__":
    main()

