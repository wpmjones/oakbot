import coc

from discord.ext import commands
from cogs.utils.constants import clans
from cogs.utils.db import get_discord_id
from config import settings


class ThRoles(commands.Cog):
    """Commands to be run during war"""
    def __init__(self, bot):
        self.bot = bot

    @coc.PlayerEvents.town_hall()
    async def on_player_townhall_upgrade(self, old_player, new_player):
        self.bot.logger.info(f"{new_player.name} changed from TH{old_player.town_hall} to TH{new_player.town_hall}")
        coc_chat = self.bot.get_channel(settings["oak_channels"]["coc_chat"])
        discord_id = get_discord_id(new_player.tag)
        guild = self.bot.get_guild(settings["discord"]["oakguild_id"])
        user = guild.get_member(discord_id)
        msg = f"Congratulations to {user.mention} on upgrading to Town Hall {new_player.town_hall}!"
        await coc_chat.send(msg)
        old_role = await self.get_th_role(old_player.town_hall)
        new_role = await self.get_th_role(new_player.town_hall)
        await user.remove_roles(old_role, reason="Auto remove from TH upgrade event")
        await user.add_roles(new_role, reason="Auto assign from TH upgrade event")

    @commands.command(name="add_th_roles")
    @commands.is_owner()
    async def add_roles(self, ctx):
        guild = self.bot.get_guild(settings["discord"]["oakguild_id"])
        clan = await self.bot.coc.get_clan(clans['Reddit Oak'])
        for member in clan.members:
            print(f"{member.name} ({member.tag})")
            discord_id = get_discord_id(member.tag)
            print(f" - {discord_id}")
            if not discord_id:
                await ctx.send(f"No linked Discord ID for {member.name} ({member.tag})")
            player = await self.bot.coc.get_player(member.tag)
            if player.town_hall < 7:
                continue
            user = guild.get_member(discord_id)
            if not user:
                self.bot.logger.debug(f"Couldn't retrieve Discord user for {player.name} ({discord_id})")
                continue
            new_role = await self.get_th_role(player.town_hall)
            await user.add_roles(new_role, reason="Auto assign from command")
            self.bot.logger.debug(f"TH{player.town_hall} role added for {player.name}")
        await ctx.send("Town hall roles added. Bam!")

    async def get_th_role(self, th_level):
        guild = self.bot.get_guild(settings["discord"]["oakguild_id"])
        role_id = settings["oak_roles"][f"TH{th_level}"]
        return guild.get_role(role_id=role_id)


def setup(bot):
    bot.add_cog(ThRoles(bot))
