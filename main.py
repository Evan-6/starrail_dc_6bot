import os
import discord
from discord.ext import commands
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING, STATE_PAUSED, STATE_STOPPED
from datetime import datetime
import asyncio

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

GIF_URL = (
    "https://images.steamusercontent.com/ugc/16515321882298826010/"
    "F9B010A05C7DF097573CC607AD8CF2F14DA0F36C/?imw=637&imh=358&ima=fit"
    "&impolicy=Letterbox&imcolor=%23000000&letterbox=true"
)

ASCII_6 = (
    "666666\n"
    "66....\n"
    "66....\n"
    "666666\n"
    "66..66\n"
    "66..66\n"
    "666666"
)

async def send_weekly_message():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("@here 記得打模擬宇宙ʕ•̫͡•ʔ•̫͡•ʔ•̫͡•ʕ•̫͡•ʔ•̫͡•ʔ")

scheduler = BackgroundScheduler()
scheduler_started = False

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

@bot.event
async def on_ready():
    print(f"✅ Bot 已登入為 {bot.user}")
    global scheduler_started
    if not scheduler_started:
        scheduler.start()
        scheduler_started = True

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content == "六":
        await message.channel.send("真是太6了")
        await message.add_reaction("6️⃣")

    elif message.content in ["真是太6了", "真是太六了"]:
        await message.channel.send("6")
        await message.add_reaction("6️⃣")

    elif message.content == "6...":
        await message.channel.send(f"```{ASCII_6}```")

    elif message.content == "3/7":
        await message.channel.send(GIF_URL)

    await bot.process_commands(message)


@bot.command(name="status", aliases=["狀態", "状态", "st"])
async def status_command(ctx: commands.Context):
    """檢查排程與頻道狀態。"""
    # Scheduler state
    state = scheduler.state
    if state == STATE_RUNNING:
        state_text = "Running"
    elif state == STATE_PAUSED:
        state_text = "Paused"
    elif state == STATE_STOPPED:
        state_text = "Stopped"
    else:
        state_text = str(state)

    # Job info
    job = scheduler.get_job("weekly_reminder")
    next_run_text = "無" if not job or not job.next_run_time else job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z")

    # Channel status
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
        f"- 目標頻道：{channel_text}\n"
        f"- 可發訊息權限：{'是' if can_send else '否'}\n"
        f"- 下一次排程：{next_run_text}\n"
        f"- 現在時間：{now_text}"
    )
    await ctx.reply(msg)

bot.run(TOKEN)
