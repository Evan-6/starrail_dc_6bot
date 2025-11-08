import discord
from discord import app_commands
from discord.ext import commands

from NEW.services.gemini_service import generate_with_gemini
from NEW.utils.memory import get_memory, clear_memory


class ChatCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    group = app_commands.Group(name="chat", description="多輪對話（短期記憶）")

    @group.command(name="start", description="開始/重設本頻道的多輪對話記憶")
    async def chat_start(self, interaction: discord.Interaction):
        clear_memory(interaction.channel_id)
        await interaction.response.send_message("已開始多輪對話，記憶已重設。", ephemeral=True)

    @group.command(name="status", description="查看記憶摘要")
    async def chat_status(self, interaction: discord.Interaction):
        mem = get_memory(interaction.channel_id)
        lines = mem.as_lines()
        text = "（空）" if not lines else "\n".join(lines[-6:])
        await interaction.response.send_message("記憶摘要（最近 6 則）：\n" + text[:1900], ephemeral=True)

    @group.command(name="stop", description="停止並清除記憶")
    async def chat_stop(self, interaction: discord.Interaction):
        clear_memory(interaction.channel_id)
        await interaction.response.send_message("已停止並清除記憶。", ephemeral=True)

    @group.command(name="say", description="帶著記憶向 Gemini 提問/對話")
    @app_commands.describe(prompt="要對話的內容", private="是否僅自己可見（預設 True）")
    async def chat_say(self, interaction: discord.Interaction, prompt: str, private: bool = True):
        await interaction.response.defer(thinking=True, ephemeral=private)
        mem = get_memory(interaction.channel_id)
        mem.add("user", prompt)

        context = "\n".join(mem.as_lines())
        sys = (
            "你是親切且精準的助理，回覆簡潔、先給答案後補充理由，"
            "若需要更多資訊可提問。避免過度客套。"
        )
        composed = f"系統：{sys}\n\n對話：\n{context}"
        reply = await generate_with_gemini(composed, max_chars=1200)
        text = reply[:1800]
        mem.add("assistant", text)
        await interaction.followup.send(text, ephemeral=private)


async def setup(bot: commands.Bot):
    cog = ChatCog(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(ChatCog.group)
    except Exception:
        pass
