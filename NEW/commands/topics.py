from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from NEW.services.gemini_service import generate_with_gemini
from NEW.utils.history import collect_channel_messages, format_messages_as_lines


class TopicsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="analyze_topics", description="主題聚類、關鍵詞、情緒比例（本頻道）")
    @app_commands.describe(
        days="統計天數（1-30），預設 7",
        private="是否僅自己可見（預設 True）",
    )
    async def analyze_topics_slash(
        self,
        interaction: discord.Interaction,
        days: app_commands.Range[int, 1, 30] = 7,
        private: bool = True,
    ):
        await interaction.response.defer(thinking=True, ephemeral=private)

        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.followup.send("僅支援文字頻道。", ephemeral=private)
            return

        after = datetime.utcnow() - timedelta(days=int(days))
        msgs = await collect_channel_messages(channel, after=after)
        lines, scanned = format_messages_as_lines(msgs)
        if not lines:
            await interaction.followup.send("沒有可分析的內容。", ephemeral=private)
            return

        header = f"🧩 主題分析（過去 {days} 天）\n掃描訊息：{scanned}"
        allowed = max(400, 1900 - len(header) - 1)

        prompt = (
            "請對以下訊息做：\n"
            "- 主題聚類（每類 1 行說明 + 關鍵詞）\n"
            "- 關鍵詞 Top 10\n"
            "- 情緒比例（正/中/負）估算\n"
            "- 重要洞察/風險提示（最多 5 點）\n\n"
            f"訊息：\n{chr(10).join(lines)}"
        )
        reply = await generate_with_gemini(prompt, max_chars=allowed)
        await interaction.followup.send(header + "\n" + reply[:allowed], ephemeral=private)


async def setup(bot: commands.Bot):
    await bot.add_cog(TopicsCog(bot))

