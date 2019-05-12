import asyncio
import traceback
from datetime import datetime
from discord.ext import commands
from config import settings

def setup(bot):
    c = WarSetup(bot)
    bot.add_cog(c)
    bot.loop.create_task(c.war_roles())
