import discord
from discord import app_commands
from discord.ext import commands

from NEW.services.gemini_service import generate_with_gemini


class LanguageCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="translate", description="翻譯文字到指定語言")
    @app_commands.describe(text="要翻譯的內容", to="目標語言（例如 zh-TW, en, ja）")
    async def translate_slash(self, interaction: discord.Interaction, text: str, to: str):
        await interaction.response.defer(thinking=True)
        prompt = (
            "你是專業翻譯。請將以下內容翻譯成指定語言，保留專有名詞並盡量自然：\n"
            f"目標語言：{to}\n\n原文：\n{text}"
        )
        reply = await generate_with_gemini(prompt, max_chars=1800)
        await interaction.followup.send(reply[:1900])

    @app_commands.command(name="polish", description="潤飾文字語氣與表達")
    @app_commands.describe(
        text="要潤飾的內容",
        tone="語氣（friendly/formal/confident/concise）",
    )
    async def polish_slash(
        self, interaction: discord.Interaction, text: str, tone: str = "concise"
    ):
        await interaction.response.defer(thinking=True)
        prompt = (
            "請潤飾以下文字，使其更清楚、有條理、語氣為指定風格；必要時分段，避免冗長。\n"
            f"語氣：{tone}\n\n文字：\n{text}"
        )
        reply = await generate_with_gemini(prompt, max_chars=1800)
        await interaction.followup.send(reply[:1900])


async def setup(bot: commands.Bot):
    await bot.add_cog(LanguageCog(bot))

