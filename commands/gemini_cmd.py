import discord
from discord import app_commands
from discord.ext import commands

from NEW.services.gemini_service import generate_with_gemini


class GeminiCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="jemini", description="使用 Google Gemini 生成文字（限制 1900 字內）")
    @app_commands.describe(prompt="輸入要詢問的內容（回覆限制 1900 字內）")
    async def jemini_slash(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer(thinking=True)
        reply = await generate_with_gemini(prompt, max_chars=1900)
        await interaction.followup.send(reply[:1900])


async def setup(bot: commands.Bot):
    await bot.add_cog(GeminiCog(bot))

