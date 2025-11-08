from datetime import datetime, timedelta
from typing import List

import discord
from discord import app_commands
from discord.ext import commands

from NEW.services.gemini_service import generate_with_gemini
from NEW.utils.history import collect_channel_messages, format_messages_as_lines


class DigestCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="digest", description="產出每日/每週 Digest 摘要（本頻道）")
    @app_commands.describe(
        period="daily 或 weekly",
        private="是否僅自己可見（預設 True）",
    )
    @app_commands.choices(
        period=[
            app_commands.Choice(name="daily", value="daily"),
            app_commands.Choice(name="weekly", value="weekly"),
        ]
    )
    async def digest_slash(
        self,
        interaction: discord.Interaction,
        period: app_commands.Choice[str],
        private: bool = True,
    ):
        await interaction.response.defer(thinking=True, ephemeral=private)

        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.followup.send("僅支援文字頻道。", ephemeral=private)
            return

        days = 1 if period.value == "daily" else 7
        after = datetime.utcnow() - timedelta(days=days)

        msgs = await collect_channel_messages(channel, after=after)
        lines, scanned = format_messages_as_lines(msgs)
        if not lines:
            await interaction.followup.send("沒有可整理的內容。", ephemeral=private)
            return

        header = f"🗞️ {channel.mention} {period.value.title()} Digest — 掃描訊息：{scanned}"
        allowed = max(400, 1900 - len(header) - 1)

        prompt = (
            "請產出 Digest：\n"
            "- 條列重點與重要貼文（附簡短理由）\n"
            "- 可列出行動清單/截止事項\n"
            "- 若過長請節錄\n\n"
            f"訊息：\n{chr(10).join(lines)}"
        )
        reply = await generate_with_gemini(prompt, max_chars=allowed)
        await interaction.followup.send(header + "\n" + reply[:allowed], ephemeral=private)


async def setup(bot: commands.Bot):
    await bot.add_cog(DigestCog(bot))

