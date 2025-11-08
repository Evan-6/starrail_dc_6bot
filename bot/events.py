import discord
from discord.ext import commands

from NEW.bot import scheduler as sched
from NEW.utils.constants import ASCII_6, GIF_URL
from NEW import config


def setup_events(bot: commands.Bot):
    @bot.event
    async def on_ready():
        print(f"✅ Bot 已登入為 {bot.user}")
        # Bind loop and ensure scheduler
        sched.bind_loop(bot.loop)
        sched.init_jobs(bot)
        sched.ensure_started()

        # Sync app commands
        try:
            guild_id = config.GUILD_ID
            if guild_id:
                guild_obj = discord.Object(id=int(guild_id))
                synced = await bot.tree.sync(guild=guild_obj)
                print(f"✅ 已同步 {len(synced)} 個 Slash 指令到伺服器 {guild_id}")
            else:
                synced = await bot.tree.sync()
                print(f"✅ 已全域同步 {len(synced)} 個 Slash 指令")
        except Exception as e:
            print(f"⚠️ Slash 指令同步失敗：{e}")

    @bot.event
    async def on_message(message: discord.Message):
        if message.author == bot.user:
            return

        if message.content == "六":
            await message.channel.send("真是太6了")
            try:
                await message.add_reaction("6️⃣")
            except Exception:
                pass
        elif message.content in ["真是太6了", "真是太六了"]:
            await message.channel.send("6")
            try:
                await message.add_reaction("6️⃣")
            except Exception:
                pass
        elif message.content == "6...":
            await message.channel.send(f"```{ASCII_6}```")
        elif message.content == "3/7":
            await message.channel.send(GIF_URL)

        await bot.process_commands(message)
