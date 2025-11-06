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
intents.members = True  # 取得成員與活動資訊
intents.presences = True  # 監聽狀態/遊戲變更

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

# 監看關鍵字（可用環境變數覆蓋，使用分號 ; 分隔）
KEYWORDS = [
    k.strip().lower()
    for k in os.getenv(
        "PRESENCE_KEYWORDS",
        "honkai;star rail;崩壞;崩坏;崩壊;星穹;星鐵;星铁",
    ).split(";")
    if k.strip()
]

# 使用者通知冷卻（分鐘）；避免洗頻
PRESENCE_COOLDOWN_MIN = int(os.getenv("PRESENCE_COOLDOWN_MIN", "120"))
_presence_last_notified = {}


def _activity_texts(activities: Iterable[discord.Activity]) -> List[str]:
    texts: List[str] = []
    for act in activities or []:
        try:
            # Custom Status 的文字在 state
            if isinstance(act, discord.CustomActivity):
                if getattr(act, "state", None):
                    texts.append(str(act.state))
            else:
                if getattr(act, "name", None):
                    texts.append(str(act.name))
        except Exception:
            continue
    return texts


def _contains_keywords(s: str) -> bool:
    t = (s or "").lower()
    return any(k in t for k in KEYWORDS)

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


@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    # 僅處理非機器人帳號
    if after.bot:
        return

    # 僅在指定頻道所屬的伺服器中觸發
    channel = bot.get_channel(CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return
    if after.guild is None or channel.guild.id != after.guild.id:
        return

    # 權限檢查
    me = channel.guild.me or channel.guild.get_member(bot.user.id)
    if not me or not channel.permissions_for(me).send_messages:
        return

    # 由「不包含」→「包含」目標字眼時才提醒
    before_hit = any(_contains_keywords(t) for t in _activity_texts(getattr(before, "activities", [])))
    after_hit = any(_contains_keywords(t) for t in _activity_texts(getattr(after, "activities", [])))
    if not after_hit or before_hit:
        return

    # 冷卻避免洗頻
    now = datetime.utcnow()
    last = _presence_last_notified.get(after.id)
    if last and (now - last).total_seconds() < PRESENCE_COOLDOWN_MIN * 60:
        return

    _presence_last_notified[after.id] = now
    try:
        await channel.send(f"{after.mention} 去讀書📚==")
    except Exception:
        pass


def _build_status_text() -> str:
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
    return msg


@bot.command(name="status", aliases=["狀態", "状态", "st"])
async def status_command(ctx: commands.Context):
    """檢查排程與頻道狀態。"""
    await ctx.reply(_build_status_text())


@bot.tree.command(name="status", description="檢查排程與頻道狀態")
async def slash_status(interaction: discord.Interaction):
    await interaction.response.send_message(_build_status_text(), ephemeral=True)

bot.run(TOKEN)
