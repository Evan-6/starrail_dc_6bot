from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from NEW.services.gemini_service import generate_with_gemini
from NEW.utils.history import collect_channel_messages, format_messages_as_lines


class SummarizeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="summarize", description="摘要本頻道最近訊息或指定天數")
    @app_commands.describe(
        days="統計天數（1-30），與 count 擇一。",
        count="最近訊息數（10-500），與 days 擇一。",
        private="是否僅自己可見（預設 True）",
    )
    async def summarize_slash(
        self,
        interaction: discord.Interaction,
        days: app_commands.Range[int, 1, 30] | None = None,
        count: app_commands.Range[int, 10, 500] | None = None,
        private: bool = True,
    ):
        await interaction.response.defer(thinking=True, ephemeral=private)

        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.followup.send("僅支援文字頻道。", ephemeral=private)
            return

        after = None
        limit = None
        if days is not None:
            after = datetime.utcnow() - timedelta(days=int(days))
        if count is not None:
            limit = int(count)
        if days is None and count is None:
            after = datetime.utcnow() - timedelta(days=7)

        msgs = await collect_channel_messages(channel, after=after, limit=limit)
        lines, scanned = format_messages_as_lines(msgs)
        if not lines:
            await interaction.followup.send("沒有可摘要的內容。", ephemeral=private)
            return

        header = (
            f"📝 摘要（{channel.mention}）\n"
            f"掃描訊息：{scanned}"
        )
        allowed = max(400, 1900 - len(header) - 1)

        prompt = (
            "請將以下訊息摘要為：\n"
            "- 重點條列（最多 10-15 行）\n"
            "- 若有討論結論/代辦事項，請列出\n\n"
            f"訊息：\n{chr(10).join(lines)}"
        )
        reply = await generate_with_gemini(prompt, max_chars=allowed)
        await interaction.followup.send(header + "\n" + reply[:allowed], ephemeral=private)


async def setup(bot: commands.Bot):
    await bot.add_cog(SummarizeCog(bot))
