import os
import discord
from discord.ext import commands
from apscheduler.schedulers.background import BackgroundScheduler
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

@scheduler.scheduled_job("cron", day_of_week="sun", hour=9, minute=0, timezone="Asia/Taipei")
def weekly_job():
    asyncio.run_coroutine_threadsafe(send_weekly_message(), bot.loop)

@bot.event
async def on_ready():
    print(f"✅ Bot 已登入為 {bot.user}")
    scheduler.start()
    await send_weekly_message()

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

bot.run(TOKEN)
