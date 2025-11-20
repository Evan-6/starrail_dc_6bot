import io
import mimetypes

import discord
from discord import app_commands
from discord.ext import commands

from NEW.services.gemini_service import generate_gemini_image


class DrawCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="draw", description="使用 Gemini 生成圖片")
    @app_commands.describe(
        prompt="輸入你想詢問或想生成的內容",
        image_size="圖片大小（預設 1K）",
        private="是否僅自己可見（預設 True）",
    )
    async def draw_slash(
        self,
        interaction: discord.Interaction,
        prompt: str,
        image_size: str = "1K",
        private: bool = True,
    ):
        # thinking 回應，是否 ephemeral 依 private 決定
        await interaction.response.defer(thinking=True, ephemeral=private)

        size = (image_size or "1K").strip() or "1K"
        text, images = await generate_gemini_image(prompt=prompt, image_size=size)

        files = []
        for idx, (data, mime) in enumerate(images):
            ext = mimetypes.guess_extension(mime or "image/png") or ".png"
            if not ext.startswith("."):
                ext = f".{ext}"
            filename = f"gemini_draw_{idx + 1}{ext}"
            files.append(discord.File(fp=io.BytesIO(data), filename=filename))

        content = (text or "").strip()
        if not content and files:
            content = "Gemini 已成功生成圖片。"
        if not content and not files:
            content = "Gemini 無法生成圖片，請更換描述內容後再試一次。"

        # Discord 訊息限制 2000 字
        if len(content) > 1900:
            content = content[:1900]

        await interaction.followup.send(
            content or "",
            files=files,
            ephemeral=private,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(DrawCog(bot))
