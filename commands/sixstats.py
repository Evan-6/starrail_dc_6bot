from datetime import datetime, timedelta
from typing import List

import discord
from discord import app_commands
from discord.ext import commands


class SixStatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="sixstats",
        description="統計過去 N 天每位使用者說了幾次 6/六（預設 7 天，僅本頻道）",
    )
    @app_commands.describe(
        days="統計天數（1-30），預設 7",
        private="是否僅自己可見（預設 True）",
    )
    async def sixstats_slash(
        self,
        interaction: discord.Interaction,
        days: app_commands.Range[int, 1, 30] = 7,
        private: bool = True,
    ):
        await interaction.response.defer(thinking=True, ephemeral=private)

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

        if len(text) > 1900:
            text = header + "\n" + "\n".join(lines)[:1800]

        await interaction.followup.send(text, ephemeral=private)


async def setup(bot: commands.Bot):
    await bot.add_cog(SixStatsCog(bot))

