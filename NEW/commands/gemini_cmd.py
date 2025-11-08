import discord
from discord import app_commands
from discord.ext import commands

from NEW.services.gemini_service import generate_with_gemini, generate_with_gemini_vision


class GeminiCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="jemini", description="使用 Google Gemini 生成文字（限制 1900 字內）")
    @app_commands.describe(prompt="輸入要詢問的內容（回覆限制 1900 字內）")
    async def jemini_slash(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer(thinking=True)
        reply = await generate_with_gemini(prompt, max_chars=1900)
        await interaction.followup.send(reply[:1900])

    @app_commands.command(name="vision", description="使用 Gemini 看圖回答（限制 1900 字內）")
    @app_commands.describe(
        prompt="輸入要詢問的內容（回覆限制 1900 字內）",
        image="上傳圖片（支援 jpg/png/webp/gif，<= 5MB）",
        private="是否僅自己可見（預設 True）",
    )
    async def vision_slash(
        self,
        interaction: discord.Interaction,
        prompt: str,
        image: discord.Attachment,
        private: bool = True,
    ):
        await interaction.response.defer(thinking=True, ephemeral=private)

        # 基本檢查與讀取圖片
        try:
            if not image:
                await interaction.followup.send("請提供一張圖片。", ephemeral=private)
                return

            mime = image.content_type or ""
            if not any(mime.startswith(x) for x in ("image/jpeg", "image/png", "image/webp", "image/gif")):
                await interaction.followup.send("不支援的圖片格式。請使用 jpg/png/webp/gif。", ephemeral=private)
                return

            # 限制 ~5MB 避免過大
            if image.size and image.size > 5 * 1024 * 1024:
                await interaction.followup.send("圖片過大（> 5MB）。請改用較小的圖片。", ephemeral=private)
                return

            data = await image.read()
        except Exception as e:
            await interaction.followup.send(f"讀取圖片失敗：{e}", ephemeral=private)
            return

        reply = await generate_with_gemini_vision(prompt, images=[(data, mime)], max_chars=1900)
        await interaction.followup.send((reply or "")[:1900], ephemeral=private)


async def setup(bot: commands.Bot):
    await bot.add_cog(GeminiCog(bot))

