import os
import discord
from discord import app_commands
from discord.ext import commands
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING, STATE_PAUSED, STATE_STOPPED
from datetime import datetime
import asyncio
from typing import List, Iterable

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

scheduler = BackgroundScheduler()
scheduler_started = False


async def send_weekly_message():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("@here 記得打模擬宇宙ʕ•̫͡•ʔ•̫͡•ʔ•̫͡•ʕ•̫͡•ʔ•̫͡•ʔ")


@scheduler.scheduled_job(
    "cron",
    day_of_week="sun",
    hour=9,
    minute=0,
    timezone="Asia/Taipei",
    id="weekly_reminder",
)
def weekly_job():
    asyncio.run_coroutine_threadsafe(send_weekly_message(), bot.loop)


async def _sync_app_commands():
    guild_id = os.getenv("GUILD_ID")
    try:
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            synced = await bot.tree.sync(guild=guild)
            print(f"✅ 已同步 {len(synced)} 個 Slash 指令到測試伺服器 {guild_id}")
        else:
            synced = await bot.tree.sync()
            print(f"✅ 已全域同步 {len(synced)} 個 Slash 指令（可能需數分鐘生效）")
    except Exception as e:
        print(f"⚠️ Slash 指令同步失敗：{e}")


@bot.event
async def on_ready():
    print(f"✅ Bot 已登入為 {bot.user}")
    global scheduler_started
    if not scheduler_started:
        scheduler.start()
        scheduler_started = True
    await _sync_app_commands()


# === Slash 指令 ===

@bot.tree.command(name="image", description="發送指定圖片網址")
@app_commands.describe(url="圖片網址")
async def send_image(interaction: discord.Interaction, url: str):
    try:
        await interaction.response.send_message(url)
    except Exception as e:
        await interaction.response.send_message(f"發送失敗：{e}", ephemeral=True)


@bot.tree.command(name="status", description="檢查排程與頻道狀態")
async def slash_status(interaction: discord.Interaction):
    state = scheduler.state
    if state == STATE_RUNNING:
        state_text = "Running"
    elif state == STATE_PAUSED:
        state_text = "Paused"
    elif state == STATE_STOPPED:
        state_text = "Stopped"
    else:
        state_text = str(state)

    job = scheduler.get_job("weekly_reminder")
    next_run_text = "無" if not job or not job.next_run_time else job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z")

    channel = bot.get_channel(CHANNEL_ID)
    channel_text = f"<#{CHANNEL_ID}>" if channel else f"(找不到頻道 {CHANNEL_ID})"

    can_send = False
    if channel and isinstance(channel, discord.TextChannel):
        me = channel.guild.me or channel.guild.get_member(bot.user.id)
        if me:
            perms = channel.permissions_for(me)
            can_send = perms.send_messages

    now_text = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    msg = (
        "📊 狀態檢查\n"
        f"- Bot：{bot.user}\n"
        f"- Scheduler：{state_text}\n"
        f"- 下一次排程：{next_run_text}\n"
    )
    await interaction.response.send_message(msg, ephemeral=True)


bot.run(TOKEN)
