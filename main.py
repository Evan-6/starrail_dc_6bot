import os
import discord
from discord import app_commands
from discord.ext import commands
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING, STATE_PAUSED, STATE_STOPPED
from datetime import datetime
import asyncio
from typing import List, Iterable
from google import genai
from google.genai import types

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

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

scheduler = BackgroundScheduler()
scheduler_started = False


# === Gemini 生成函式 ===
async def generate_with_gemini(prompt: str) -> str:
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        model = "gemini-2.5-flash"

        contents = [
            types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        ]
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
            image_config=types.ImageConfig(image_size="1K"),
        )

        text = ""
        for chunk in client.models.generate_content_stream(
            model=model, contents=contents, config=config
        ):
            if chunk.text:
                text += chunk.text
        return text.strip() or "（無回覆）"
    except Exception as e:
        return f"Gemini 錯誤：{e}"


async def send_weekly_message():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("@here 記得打模擬宇宙ʕ•̫͡•ʔ•̫͡•ʔ•̫͡•ʕ•̫͡•ʔ•̫͡•ʔ")


# === 定時排程 ===
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


# === 關鍵字監聽 ===
KEYWORDS = [
    k.strip().lower()
    for k in os.getenv(
        "PRESENCE_KEYWORDS",
        "honkai;star rail;崩壞;崩坏;崩壊;星穹;星鐵;星铁",
    ).split(";")
    if k.strip()
]
PRESENCE_COOLDOWN_MIN = int(os.getenv("PRESENCE_COOLDOWN_MIN", "120"))
_presence_last_notified = {}


def _activity_texts(acts: Iterable[discord.Activity]) -> List[str]:
    texts = []
    for a in acts or []:
        if isinstance(a, discord.CustomActivity):
            if getattr(a, "state", None):
                texts.append(str(a.state))
        elif getattr(a, "name", None):
            texts.append(str(a.name))
    return texts


def _contains_keywords(s: str) -> bool:
    return any(k in (s or "").lower() for k in KEYWORDS)


# === 應用程式同步 ===
async def _sync_app_commands():
    guild_id = os.getenv("GUILD_ID")
    try:
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            synced = await bot.tree.sync(guild=guild)
            print(f"✅ 已同步 {len(synced)} 個 Slash 指令到伺服器 {guild_id}")
        else:
            synced = await bot.tree.sync()
            print(f"✅ 已全域同步 {len(synced)} 個 Slash 指令")
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


# @bot.event
# async def on_presence_update(before, after):
#     if after.bot:
#         return
#     channel = bot.get_channel(CHANNEL_ID)
#     if not isinstance(channel, discord.TextChannel):
#         return
#     if after.guild is None or channel.guild.id != after.guild.id:
#         return

#     me = channel.guild.me or channel.guild.get_member(bot.user.id)
#     if not me or not channel.permissions_for(me).send_messages:
#         return

#     before_hit = any(_contains_keywords(t) for t in _activity_texts(before.activities))
#     after_hit = any(_contains_keywords(t) for t in _activity_texts(after.activities))
#     if not after_hit or before_hit:
#         return

#     now = datetime.utcnow()
#     last = _presence_last_notified.get(after.id)
#     if last and (now - last).total_seconds() < PRESENCE_COOLDOWN_MIN * 60:
#         return

#     _presence_last_notified[after.id] = now
#     await channel.send(f"{after.mention} 去讀書📚==")


# === 狀態文字 ===
def _build_status_text() -> str:
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
    next_run = (
        "無"
        if not job or not job.next_run_time
        else job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    )
    now_text = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"📊 狀態\n- Scheduler：{state_text}\n- 下一次排程：{next_run}\n- 現在時間：{now_text}"


@bot.command(name="status")
async def status_command(ctx):
    await ctx.reply(_build_status_text())


@bot.tree.command(name="status", description="檢查排程與頻道狀態")
async def slash_status(interaction: discord.Interaction):
    await interaction.response.send_message(_build_status_text(), ephemeral=True)


# === 新增 Slash 指令 ===

@bot.tree.command(name="say", description="讓 Bot 說話")
@app_commands.describe(text="要說的內容")
async def slash_say(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(text)


@bot.tree.command(name="jemini", description="使用 Google Gemini 生成文字")
@app_commands.describe(prompt="輸入要詢問的內容")
async def slash_jemini(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer(thinking=True)
    reply = await generate_with_gemini(prompt)
    await interaction.followup.send(reply[:1900])


bot.run(TOKEN)
