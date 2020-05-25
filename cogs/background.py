from discord.ext import commands, tasks
from cogs.utils.constants import clans
from cogs.utils.db import get_discord_id
from config import settings


class Background(commands.Cog):
    """Cog for background tasks. No real commands here."""
    def __init__(self, bot):
        self.bot = bot
        self.guild = None
        self.check_quercus.start()

    def cog_unload(self):
        self.check_quercus.cancel()

    async def cog_init_ready(self) -> None:
        """Sets the guild properly"""
        await self.bot.wait_until_ready()
        if not self.guild:
            self.guild = self.bot.get_guild(settings['discord']['oakguild_id'])

    @tasks.loop(hours=2.0)
    async def check_quercus(self):
        clan = await self.bot.coc.get_clan(clans['Reddit Quercus'])
        quercus_role = self.guild.get_role(settings['oak_roles']['quercus'])
        not_in_links = []
        for member in clan.members:
            try:
                discord_id = get_discord_id(member.tag)
                discord_member = self.guild.get_member(discord_id)
                if quercus_role not in discord_member.roles:
                    await discord_member.add_roles(quercus_role, "Auto-add in background. You're welcome!")
            except ValueError:
                not_in_links.append(f"{member.name} ({member.tag})")
        if not_in_links:
            channel = self.guild.get_channel(settings['oak_roles']['test_chat'])
            new_line = "\n"
            await channel.send(f"The following players in Quercus are not in the links API:\n"
                               f"{new_line.join(not_in_links)}")

    @tasks.loop(hours=1.0)
    async def check_oak(self):
        clan = await self.bot.coc.get_clan(clans['Reddit Oak'])
        quercus_role = self.guild.get_role(settings['oak_roles']['quercus'])
        not_in_links = []
        for member in clan.members:
            try:
                discord_id = get_discord_id(member.tag)
                discord_member = self.guild.get_member(discord_id)
                if quercus_role in discord_member.roles:
                    await discord_member.remove_roles(quercus_role, "Auto-remove in background because player is back "
                                                                    "in Oak. You're welcome!")
            except ValueError:
                not_in_links.append(f"{member.name} ({member.tag})")
        if not_in_links:
            channel = self.guild.get_channel(settings['oak_roles']['test_chat'])
            new_line = "\n"
            await channel.send(f"The following players in Oak are not in the links API:\n"
                               f"{new_line.join(not_in_links)}")


def setup(bot):
    bot.add_cog(Background(bot))
