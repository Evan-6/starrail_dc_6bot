import discord
from discord import app_commands
from discord.ext import commands


class SayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="say", description="讓 Bot 說話")
    @app_commands.describe(text="要說的內容")
    async def say_slash(self, interaction: discord.Interaction, text: str):
        await interaction.response.send_message(text)


async def setup(bot: commands.Bot):
    await bot.add_cog(SayCog(bot))

