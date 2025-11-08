from datetime import datetime, timedelta
from typing import List

import discord
from discord import app_commands
from discord.ext import commands

from NEW.services.gemini_service import generate_with_gemini
from NEW.utils.text import shorten


class AskDocCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="askdoc", description="以本頻道釘選/近期訊息作為知識庫來回答")
    @app_commands.describe(
        question="問題/需求",
        use_pins="是否使用釘選訊息（預設 True）",
        days="若不使用釘選，改用最近 N 天訊息（1-30，預設 7）",
        private="是否僅自己可見（預設 True）",
    )
    async def askdoc_slash(
        self,
        interaction: discord.Interaction,
        question: str,
        use_pins: bool = True,
        days: app_commands.Range[int, 1, 30] = 7,
        private: bool = True,
    ):
        await interaction.response.defer(thinking=True, ephemeral=private)

        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.followup.send("僅支援文字頻道。", ephemeral=private)
            return

        entries: List[str] = []
        scanned = 0
        max_context_chars = 11000

        try:
            if use_pins:
                pins = await channel.pins()
                for msg in pins:
                    scanned += 1
                    content = (msg.content or "").strip()
                    if not content:
                        continue
                    ts = msg.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                    author = getattr(msg.author, "display_name", str(msg.author))
                    line = f"- [PIN {ts}] {author}: {shorten(content, 260)}"
                    if sum(len(x) + 1 for x in entries) + len(line) + 1 > max_context_chars:
                        break
                    entries.append(line)
            else:
                start_time = datetime.utcnow() - timedelta(days=int(days))
                async for msg in channel.history(after=start_time, limit=None, oldest_first=False):
                    scanned += 1
                    if msg.author.bot:
                        continue
                    content = (msg.content or "").strip()
                    if not content:
                        continue
                    ts = msg.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                    author = getattr(msg.author, "display_name", str(msg.author))
                    line = f"- [{ts}] {author}: {shorten(content, 260)}"
                    if sum(len(x) + 1 for x in entries) + len(line) + 1 > max_context_chars:
                        break
                    entries.append(line)
        except Exception as e:
            await interaction.followup.send(f"讀取訊息時發生錯誤：{e}", ephemeral=private)
            return

        if not entries:
            await interaction.followup.send("沒有可用的知識內容。", ephemeral=private)
            return

        header = (
            "📚 AskDoc\n"
            + ("來源：釘選訊息" if use_pins else f"來源：最近 {days} 天")
            + f"，掃描訊息：{scanned}"
        )
        allowed = max(400, 1900 - len(header) - 1)

        prompt = (
            "你是問答助手。僅根據下列提供的內容回答使用者的問題；"
            "若無足夠資訊請誠實說明『無法判定』並建議需要的補充。請精簡作答。\n\n"
            f"使用者問題：{question}\n\n"
            f"知識內容：\n{chr(10).join(entries)}"
        )
        reply = await generate_with_gemini(prompt, max_chars=allowed)
        await interaction.followup.send(header + "\n" + reply[:allowed], ephemeral=private)


async def setup(bot: commands.Bot):
    await bot.add_cog(AskDocCog(bot))

