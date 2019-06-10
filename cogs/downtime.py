import asyncio
import discord
from discord.ext import commands
from datetime import datetime


class Downtime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.downtime = datetime(2019, 6, 11, 2, 15)
        self.bg_task = self.bot.loop.create_task(self.main())

    async def main(self):
        while datetime.now() < self.downtime:
            upcoming = self.downtime - datetime.now()
            for channel in self.bot.get_all_channels():
                if channel.name == "coc-chat":
                    try:
                        await channel.send(f"The Arborist will be napping for maintenance "
                                           f"in {upcoming.seconds // 3600} hours "
                                           f"and {(upcoming.seconds // 60) % 60} minutes. "
                                           f"The nap should last about 30 minutes.")
                    except discord.Forbidden:
                        print(f"Didn't have perms for {channel.name} on {channel.guild.name}.")
            print("done")
            await asyncio.sleep(30*60)


def setup(bot):
    bot.add_cog(Downtime(bot))
