from datetime import datetime, timedelta
from typing import List

import discord
from discord import app_commands
from discord.ext import commands

from NEW.services.gemini_service import generate_with_gemini
from NEW.utils.text import shorten


class AnalyzeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="analyze",
        description="使用 Gemini 對本頻道 N 天訊息進行自訂分析",
    )
    @app_commands.describe(
        instruction="給 Gemini 的分析指令/提問",
        days="統計天數（1-30），預設 7",
        private="是否僅自己可見（預設 True）",
    )
    async def analyze_slash(
        self,
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
                line = f"- [{ts}] {author}: {shorten(content, 260)}"
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
            "避免臆測或引用不存在的資訊。若無法判定請明確標註『無法判定』；若內容過長，請摘要。"
        ) + (
            f"\n\n使用者指令：{instruction}\n\n"
            f"訊息上下文（過去 {days} 天，僅節錄）：\n{context_block}"
        )

        reply = await generate_with_gemini(composed_prompt, max_chars=allowed)
        text = header + "\n" + (reply or "")[:allowed]
        await interaction.followup.send(text, ephemeral=private)


async def setup(bot: commands.Bot):
    await bot.add_cog(AnalyzeCog(bot))

