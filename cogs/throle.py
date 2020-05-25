from discord.ext import commands
from config import settings


class ThRoles(commands.Cog):
    """Commands to be run during war"""
    def __init__(self, bot):
        self.bot = bot
        self.guild = None
        self.bot.coc.add_events(self.on_player_townhall_upgrade)
        self.bot.coc.start_updates("player")
        bot.loop.create_task(self.cog_init_ready())

    def cog_unload(self):
        self.bot.coc.remove_events(self.on_player_townhall_upgrade)

    async def cog_init_ready(self):
        """Sets the guild properly"""
        await self.bot.wait_until_ready()
        if not self.guild:
            self.guild = self.bot.get_guild(settings["discord"]["oakguild_id"])

    async def on_player_townhall_upgrade(self, old_th, new_th, player):
        self.bot.logger.info(f"{player} from {old_th} to {new_th}")
        conn = self.bot.pool
        coc_chat = self.bot.get_channel(settings["oak_channels"]["coc_chat"])
        sql = "SELECT discord_id FROM rcs_discord_links WHERE player_tag = $1"
        row = await conn.fetchrow(sql, player.tag[1:])
        discord_id = row["discord_id"]
        if not self.guild:
            self.guild = self.bot.get_guild(settings["discord"]["oakguild_id"])
        user = self.guild.get_member(discord_id)
        msg = f"Congratulations to <@{user.mention} on upgrading to Town Hall {new_th}!"
        await coc_chat.send(msg)
        old_role = await self.get_th_role(old_th)
        new_role = await self.get_th_role(new_th)
        await user.remove_roles(old_role, reason="Auto remove from TH upgrade event")
        await user.add_roles(new_role, reason="Auto assign from TH upgrade event")

    @commands.command(name="add_th_roles")
    @commands.is_owner()
    async def add_roles(self, ctx):
        conn = self.bot.pool
        sql = "SELECT discord_id, '#' || player_tag as player_tag FROM rcs_discord_links"
        rows = await conn.fetch(sql)
        for player in rows:
            member = await self.bot.coc.get_player(player["player_tag"])
            if member.town_hall < 7:
                continue
            if member.clan and member.clan.tag != "#CVCJR89":
                continue
            user = self.guild.get_member(player["discord_id"])
            if not user:
                continue
            new_role = await self.get_th_role(member.town_hall)
            await user.add_roles(new_role, reason="Auto assign from command")
            self.bot.logger.debug(f"TH{member.town_hall} role added for {member.name}")
        await ctx.send("Town hall roles added. Bam!")

    async def get_th_role(self, th_level):
        role_id = settings["oak_roles"][f"TH{th_level}"]
        return self.guild.get_role(role_id=role_id)


def setup(bot):
    bot.add_cog(ThRoles(bot))
