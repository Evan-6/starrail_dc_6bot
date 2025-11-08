import discord
from discord import app_commands
from discord.ext import commands

from NEW.services.gemini_service import generate_with_gemini


class ModerateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="moderate", description="內容審核：分類並給出簡短理由")
    @app_commands.describe(text="要檢查的文字內容", private="是否僅自己可見（預設 True）")
    async def moderate_slash(self, interaction: discord.Interaction, text: str, private: bool = True):
        await interaction.response.defer(thinking=True, ephemeral=private)
        prompt = (
            "請作為內容審核助手，判斷以下文字是否含有：仇恨/霸凌、色情/NSFW、騷擾/威脅、詐騙/廣告、個資洩漏、版權疑慮。"
            "請輸出簡短條列，僅列出命中的項目與理由；若無命中，請回覆『未發現明顯問題』。\n\n"
            f"文字：\n{text}"
        )
        reply = await generate_with_gemini(prompt, max_chars=1200)
        await interaction.followup.send(reply[:1900], ephemeral=private)


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerateCog(bot))

