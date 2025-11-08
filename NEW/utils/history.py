from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Tuple

import discord

from NEW.utils.text import shorten


async def collect_channel_messages(
    channel: discord.TextChannel,
    after: datetime | None = None,
    limit: int | None = None,
    include_bots: bool = False,
) -> List[discord.Message]:
    msgs: List[discord.Message] = []
    async for msg in channel.history(after=after, limit=limit, oldest_first=False):
        if not include_bots and msg.author.bot:
            continue
        if (msg.content or "").strip() or msg.attachments:
            msgs.append(msg)
    return msgs


def format_messages_as_lines(
    messages: Iterable[discord.Message],
    max_context_chars: int = 12000,
    max_line_len: int = 260,
) -> Tuple[List[str], int]:
    lines: List[str] = []
    scanned = 0
    for msg in messages:
        scanned += 1
        content = (msg.content or "").strip()
        if not content and msg.attachments:
            content = "[附件] " + ", ".join(a.filename for a in msg.attachments)
        ts = msg.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        author = getattr(msg.author, "display_name", str(msg.author))
        line = f"- [{ts}] {author}: {shorten(content, max_line_len)}"
        if sum(len(x) + 1 for x in lines) + len(line) + 1 > max_context_chars:
            break
        lines.append(line)
    return lines, scanned

