import os
import re
import discord
from discord import app_commands
from discord.ext import commands
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING, STATE_PAUSED, STATE_STOPPED
from datetime import datetime, timedelta
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
async def generate_with_gemini(prompt: str, max_chars: int = 1800) -> str:
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        model = "gemini-2.5-flash"

        # 統一於提示中提出需求，包含長度限制與風格
        requirements = (
            f"需求：\n"
            f"- 回覆長度請控制在 {max_chars} 個字元以內（含 Markdown 符號）。\n"
            f"- 若內容過長，請摘要重點。\n"
            f"- 請避免多餘前言與客套，專注結果本身。\n"
        )
        final_prompt = f"{requirements}\n任務：\n{prompt}"

        contents = [
            types.Content(role="user", parts=[types.Part.from_text(text=final_prompt)])
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
        text = (text or "").strip()
        if len(text) > max_chars:
            text = text[:max_chars]
        return text or "（無回覆）"
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


@bot.tree.command(name="jemini", description="使用 Google Gemini 生成文字（限制 1900 字內）")
@app_commands.describe(prompt="輸入要詢問的內容（回覆限制 1900 字內）")
async def slash_jemini(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer(thinking=True)
    reply = await generate_with_gemini(prompt, max_chars=1900)
    await interaction.followup.send(reply[:1900])


@bot.tree.command(
    name="sixstats",
    description="統計過去 N 天每位使用者說了幾次 6/六（預設 7 天，僅本頻道）",
)
@app_commands.describe(
    days="統計天數（1-30），預設 7",
    private="是否僅自己可見（預設 True）",
)
async def slash_sixstats(
    interaction: discord.Interaction,
    days: app_commands.Range[int, 1, 30] = 7,
    private: bool = True,
):
    # 延遲回覆以避免逾時
    await interaction.response.defer(thinking=True, ephemeral=private)

    # 計算起始時間
    start_time = datetime.utcnow() - timedelta(days=int(days))

    channel = interaction.channel
    if channel is None:
        await interaction.followup.send("找不到頻道。", ephemeral=private)
        return

    counts = {}
    scanned = 0

    try:
        async for msg in channel.history(after=start_time, limit=None, oldest_first=False):
            scanned += 1
            if msg.author.bot:
                continue
            content = msg.content or ""
            # 每個訊息只計一次（含有任一關鍵字即+1）
            if ("6" in content) or ("六" in content):
                counts[msg.author.id] = counts.get(msg.author.id, 0) + 1
    except Exception as e:
        await interaction.followup.send(f"讀取訊息時發生錯誤：{e}", ephemeral=private)
        return

    if not counts:
        await interaction.followup.send(
            f"過去 {days} 天內，本頻道沒有出現『6/六』。",
            ephemeral=private,
        )
        return

    # 依次數排序
    sorted_items = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)

    lines = []
    for idx, (user_id, cnt) in enumerate(sorted_items[:30], start=1):
        name = None
        if interaction.guild:
            member = interaction.guild.get_member(user_id)
            if member:
                name = member.display_name
        display = name or f"<@{user_id}>"
        lines.append(f"{idx}. {display}：{cnt}")

    header = (
        f"📈 過去 {days} 天本頻道『6/六』訊息計數（每則訊息最多算一次）\n"
        f"（僅統計文字訊息，忽略機器人）\n"
        f"共掃描訊息：{scanned}"
    )
    text = header + "\n" + "\n".join(lines)

    # 2000 字符限制處理
    if len(text) > 1900:
        text = header + "\n" + "\n".join(lines)[:1800]

    await interaction.followup.send(text, ephemeral=private)


@bot.tree.command(
    name="codes",
    description="使用 Gemini 彙整 N 天內的兌換碼（全伺服器）",
)
@app_commands.describe(
    days="統計天數（1-30），預設 7",
    private="是否僅自己可見（預設 True）",
)
async def slash_codes(
    interaction: discord.Interaction,
    days: app_commands.Range[int, 1, 30] = 7,
    private: bool = True,
):
    await interaction.response.defer(thinking=True, ephemeral=private)

    start_time = datetime.utcnow() - timedelta(days=int(days))
    guild = interaction.guild
    me = guild.me if guild else None

    # 關鍵字與樣式
    redeem_keywords = [
        "兌換碼",
        "兑换码",
        "兌換序號",
        "兌換序号",
        "兑换序号",
        "序號",
        "序号",
        "禮包碼",
        "礼包码",
        "兌換",
        "兑换",
    ]
    code_pattern = re.compile(r"(?<![A-Z0-9])[A-Z0-9]{7,18}(?![A-Z0-9])")

    collected = []
    scanned = 0
    matched = 0
    errors = []

    channels: List[discord.TextChannel] = []
    if guild:
        # 僅蒐集文字頻道且可讀取歷史
        for ch in guild.text_channels:
            try:
                perms = ch.permissions_for(me) if me else None
                if perms and perms.read_message_history and perms.read_messages:
                    channels.append(ch)
            except Exception:
                continue
    else:
        if isinstance(interaction.channel, discord.TextChannel):
            channels = [interaction.channel]

    max_collect = 400
    max_context_chars = 12000

    for ch in channels:
        try:
            async for msg in ch.history(after=start_time, limit=None, oldest_first=False):
                scanned += 1
                content = (msg.content or "").strip()
                if not content:
                    continue
                lower = content.lower()
                has_kw = any(k in lower for k in redeem_keywords)
                has_code = bool(code_pattern.search(content.upper()))
                if has_kw or has_code:
                    matched += 1
                    collected.append(
                        dict(
                            channel=ch,
                            author=msg.author,
                            created_at=msg.created_at,
                            content=content,
                            jump_url=msg.jump_url,
                        )
                    )
                    if len(collected) >= max_collect:
                        break
        except Exception as e:
            errors.append(f"#{ch.name}: {e}")
        if len(collected) >= max_collect:
            break

    if not collected:
        await interaction.followup.send(
            f"過去 {days} 天未找到可能含『兌換碼』的訊息。掃描訊息：{scanned}。",
            ephemeral=private,
        )
        return

    # 準備給 Gemini 的上下文
    def _shorten(s: str, n: int = 260) -> str:
        s = s.replace("\n", " ")
        return (s[: n - 1] + "…") if len(s) > n else s

    lines = []
    for item in collected:
        ts = item["created_at"].strftime("%Y-%m-%d %H:%M:%S UTC")
        ch_name = f"#{item['channel'].name}"
        author = getattr(item["author"], "display_name", str(item["author"]))
        snippet = _shorten(item["content"], 260)
        lines.append(f"- [{ts}] {ch_name} {author}: {snippet}")
        if sum(len(x) + 1 for x in lines) > max_context_chars:
            lines.pop()  # remove last if exceeded
            break

    context_block = "\n".join(lines)

    header = (
        f"📋 兌換碼整理（過去 {days} 天）\n"
        f"掃描訊息：{scanned}，符合關鍵：{matched}，來源頻道數：{len(channels)}"
    )
    # 根據標頭長度計算可用內容長度，避免超過訊息上限
    allowed = max(400, 1900 - len(header) - 1)

    prompt = (
        "你是資料整理助手。從以下訊息中擷取所有明確的『兌換碼』，"
        "整理為 Markdown 表格，欄位：代碼｜遊戲/平台｜獎勵（簡短）｜是否有效/過期（若可辨識）｜來源（#頻道/作者/UTC 時間）｜備註（可空）。"
        "去除重複代碼，避免編造未知資訊；無法判定者留空。若表格過長，請摘要重點代碼。\n\n"
        f"訊息（過去 {days} 天，僅節錄）：\n{context_block}"
    )

    reply = await generate_with_gemini(prompt, max_chars=allowed)

    text = header + "\n" + reply[:allowed]
    await interaction.followup.send(text, ephemeral=private)


@bot.tree.command(
    name="analyze",
    description="使用 Gemini 對本頻道 N 天訊息進行自訂分析",
)
@app_commands.describe(
    instruction="給 Gemini 的分析指令/提問",
    days="統計天數（1-30），預設 7",
    private="是否僅自己可見（預設 True）",
)
async def slash_analyze(
    interaction: discord.Interaction,
    instruction: str,
    days: app_commands.Range[int, 1, 30] = 7,
    private: bool = True,
):
    await interaction.response.defer(thinking=True, ephemeral=private)

    start_time = datetime.utcnow() - timedelta(days=int(days))

    channel = interaction.channel
    if channel is None:
        await interaction.followup.send("找不到頻道。", ephemeral=private)
        return

    scanned = 0
    max_context_chars = 12000

    def _shorten(s: str, n: int = 260) -> str:
        s = (s or "").replace("\n", " ")
        return (s[: n - 1] + "…") if len(s) > n else s

    lines: List[str] = []
    try:
        async for msg in channel.history(after=start_time, limit=None, oldest_first=False):
            scanned += 1
            if msg.author.bot:
                continue
            content = (msg.content or "").strip()
            if not content:
                continue
            ts = msg.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            author = getattr(msg.author, "display_name", str(msg.author))
            line = f"- [{ts}] {author}: {_shorten(content, 260)}"
            # 控制總字元數
            if sum(len(x) + 1 for x in lines) + len(line) + 1 > max_context_chars:
                break
            lines.append(line)
    except Exception as e:
        await interaction.followup.send(f"讀取訊息時發生錯誤：{e}", ephemeral=private)
        return

    if not lines:
        await interaction.followup.send(
            f"過去 {days} 天本頻道沒有可用的文字訊息可分析。掃描訊息：{scanned}。",
            ephemeral=private,
        )
        return

    context_block = "\n".join(lines)

    header = (
        f"🧠 自訂分析（本頻道，過去 {days} 天）\n"
        f"掃描訊息：{scanned}"
    )

    allowed = max(400, 1900 - len(header) - 1)

    composed_prompt = (
        "你是資料分析助手。請嚴格依照使用者的指令，僅根據提供的訊息內容進行分析與回答，"
        "避免臆測或引用不存在的資訊。若無法判定請明確標註『無法判定』；若內容過長，請摘要。") + (
        f"\n\n使用者指令：{instruction}\n\n"
        f"訊息上下文（過去 {days} 天，僅節錄）：\n{context_block}"
    )

    reply = await generate_with_gemini(composed_prompt, max_chars=allowed)

    text = header + "\n" + (reply or "")[:allowed]
    await interaction.followup.send(text, ephemeral=private)


bot.run(TOKEN)
