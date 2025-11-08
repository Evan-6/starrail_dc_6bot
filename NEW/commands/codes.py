import re
from datetime import datetime, timedelta
from typing import Dict, List, Set

import discord
from discord import app_commands
from discord.ext import commands

from NEW.services.gemini_service import generate_with_gemini
from NEW.utils.text import shorten


class CodesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="codes",
        description="使用 Gemini 彙整 N 天內的兌換碼（全伺服器）",
    )
    @app_commands.describe(
        days="統計天數（1-30），預設 7",
        private="是否僅自己可見（預設 True）",
    )
    async def codes_slash(
        self,
        interaction: discord.Interaction,
        days: app_commands.Range[int, 1, 30] = 7,
        private: bool = True,
    ):
        await interaction.response.defer(thinking=True, ephemeral=private)

        start_time = datetime.utcnow() - timedelta(days=int(days))
        guild = interaction.guild
        me = guild.me if guild else None

        redeem_keywords = [
            "兌換碼",
            "兑换码",
            "兌換序號",
            "兌換序号",
            "兑换序号",
            "序號",
            "序号",
            "禮包碼",
            "礼包码",
            "兌換",
            "兑换",
        ]
        code_pattern = re.compile(r"(?<![A-Z0-9])[A-Z0-9]{7,18}(?![A-Z0-9])")

        collected = []
        scanned = 0
        matched = 0
        errors = []

        channels: List[discord.TextChannel] = []
        if guild:
            for ch in guild.text_channels:
                try:
                    perms = ch.permissions_for(me) if me else None
                    if perms and perms.read_message_history and perms.read_messages:
                        channels.append(ch)
                except Exception:
                    continue
        else:
            if isinstance(interaction.channel, discord.TextChannel):
                channels = [interaction.channel]

        max_collect = 400
        max_context_chars = 12000

        for ch in channels:
            try:
                async for msg in ch.history(after=start_time, limit=None, oldest_first=False):
                    scanned += 1
                    content = (msg.content or "").strip()
                    if not content:
                        continue
                    lower = content.lower()
                    has_kw = any(k in lower for k in redeem_keywords)
                    has_code = bool(code_pattern.search(content.upper()))
                    if has_kw or has_code:
                        matched += 1
                        collected.append(
                            dict(
                                channel=ch,
                                author=msg.author,
                                created_at=msg.created_at,
                                content=content,
                                jump_url=msg.jump_url,
                            )
                        )
                        if len(collected) >= max_collect:
                            break
            except Exception as e:
                errors.append(f"#{ch.name}: {e}")
            if len(collected) >= max_collect:
                break

        if not collected:
            await interaction.followup.send(
                f"過去 {days} 天未找到可能含『兌換碼』的訊息。掃描訊息：{scanned}。",
                ephemeral=private,
            )
            return

        # 先抽取代碼並去重
        code_to_sources: Dict[str, List[str]] = {}
        seen_codes: Set[str] = set()
        for item in collected:
            content_up = (item["content"] or "").upper()
            for m in code_pattern.finditer(content_up):
                code = m.group(0)
                seen_codes.add(code)
                src = f"#{item['channel'].name} @ {item['created_at'].strftime('%Y-%m-%d')}"
                code_to_sources.setdefault(code, []).append(src)

        # 組合給 Gemini 的上下文（訊息節錄 + 代碼清單）
        lines = []
        for item in collected:
            ts = item["created_at"].strftime("%Y-%m-%d %H:%M:%S UTC")
            ch_name = f"#{item['channel'].name}"
            author = getattr(item["author"], "display_name", str(item["author"]))
            snippet = shorten(item["content"], 260)
            lines.append(f"- [{ts}] {ch_name} {author}: {snippet}")
            if sum(len(x) + 1 for x in lines) > max_context_chars:
                lines.pop()
                break

        context_block = "\n".join(lines)

        header = (
            f"📋 兌換碼整理（過去 {days} 天）\n"
            f"掃描訊息：{scanned}，符合關鍵：{matched}，來源頻道數：{len(channels)}\n"
            f"去重後代碼數：{len(seen_codes)}"
        )
        allowed = max(400, 1900 - len(header) - 1)

        # 附上機器先抽取的代碼清單以輔助準確
        auto_codes_block = "\n".join(
            f"- {c}（出處：{', '.join(srcs[:3])}{'…' if len(srcs) > 3 else ''})" for c, srcs in code_to_sources.items()
        ) or "（無機器抽取結果）"

        now_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        prompt = (
            "你是資料整理助手。從以下訊息中擷取所有明確的『兌換碼』，"
            "整理為 Markdown 表格，欄位：代碼｜遊戲/平台｜獎勵（簡短）｜是否有效/過期（若可辨識）｜來源（#頻道/作者/UTC 時間）｜備註（可空）。"
            "去除重複代碼，避免編造未知資訊；無法判定者留空。若表格過長，請摘要重點代碼。\n\n"
            f"現在時間（供參考）：{now_utc}\n\n"
            f"機器先抽取代碼（供參考）：\n{auto_codes_block}\n\n"
            f"訊息（過去 {days} 天，僅節錄）：\n{context_block}"
        )

        reply = await generate_with_gemini(prompt, max_chars=allowed)
        text = header + "\n" + reply[:allowed]
        await interaction.followup.send(text, ephemeral=private)


async def setup(bot: commands.Bot):
    await bot.add_cog(CodesCog(bot))

