import discord
from discord import app_commands
from discord.ext import commands

from NEW.bot.scheduler import status_text


class StatusCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="status")
    async def status_prefix(self, ctx: commands.Context):
        await ctx.reply(status_text())

    @app_commands.command(name="status", description="檢查排程與頻道狀態")
    async def status_slash(self, interaction: discord.Interaction):
        await interaction.response.send_message(status_text(), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(StatusCog(bot))

