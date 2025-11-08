import discord
from discord.ext import commands

from NEW import config


def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True
    intents.members = True
    intents.presences = True

    bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents)
    return bot

