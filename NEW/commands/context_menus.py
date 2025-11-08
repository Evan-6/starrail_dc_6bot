import discord
from discord import app_commands
from discord.ext import commands

from NEW.services.gemini_service import generate_with_gemini
from NEW.utils.text import shorten


class ContextMenusCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.context_menu(name="Summarize with Gemini")
    async def summarize_message(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(thinking=True, ephemeral=True)
        snippet = shorten(message.content or "", 2000)
        prompt = (
            "請以要點條列精簡摘要以下訊息的重點，最多 12 行，必要時附上下一步建議。\n\n"
            f"訊息：\n{snippet}"
        )
        reply = await generate_with_gemini(prompt, max_chars=1200)
        await interaction.followup.send(reply[:1900], ephemeral=True)

    @app_commands.context_menu(name="Reply with Gemini")
    async def reply_with_gemini(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(thinking=True, ephemeral=True)
        snippet = shorten(message.content or "", 2000)
        prompt = (
            "根據以下訊息內容，撰寫一則合適且禮貌的回覆，"
            "可提出建設性建議或解法。請避免過度客套，直接進入重點。\n\n"
            f"訊息：\n{snippet}"
        )
        reply = await generate_with_gemini(prompt, max_chars=1200)
        await interaction.followup.send("建議回覆：\n" + reply[:1800], ephemeral=True)

    @app_commands.context_menu(name="Moderate Message")
    async def moderate_message(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(thinking=True, ephemeral=True)
        snippet = shorten(message.content or "", 2000)
        prompt = (
            "請作為內容審核助手，判斷以下文字是否含有：仇恨/霸凌、色情/NSFW、騷擾/威脅、詐騙/廣告、個資洩漏、版權疑慮。"
            "請輸出簡短條列，僅列出命中的項目與理由；若無命中，請回覆『未發現明顯問題』。\n\n"
            f"訊息：\n{snippet}"
        )
        reply = await generate_with_gemini(prompt, max_chars=900)
        await interaction.followup.send(reply[:1900], ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ContextMenusCog(bot))

