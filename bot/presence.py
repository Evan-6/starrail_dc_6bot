from datetime import datetime
from typing import Dict

import discord
from discord.ext import commands

from NEW import config
from NEW.utils.text import activity_texts, contains_any


class PresenceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._last_notified: Dict[int, datetime] = {}

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if after.bot:
            return

        channel_id = config.CHANNEL_ID
        if not channel_id:
            return

        channel = self.bot.get_channel(int(channel_id))
        if not isinstance(channel, discord.TextChannel):
            return

        if after.guild is None or channel.guild.id != after.guild.id:
            return

        me = channel.guild.me or channel.guild.get_member(self.bot.user.id)
        if not me or not channel.permissions_for(me).send_messages:
            return

        before_hit = any(contains_any(t, config.PRESENCE_KEYWORDS) for t in activity_texts(before.activities))
        after_hit = any(contains_any(t, config.PRESENCE_KEYWORDS) for t in activity_texts(after.activities))
        if not after_hit or before_hit:
            return

        now = datetime.utcnow()
        last = self._last_notified.get(after.id)
        if last and (now - last).total_seconds() < config.PRESENCE_COOLDOWN_MIN * 60:
            return

        self._last_notified[after.id] = now
        await channel.send(f"{after.mention} 去讀書📚==")


async def setup(bot: commands.Bot):
    await bot.add_cog(PresenceCog(bot))

