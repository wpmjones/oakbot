from discord.ext import commands
from config import settings


class ThRoles(commands.Cog):
    """Commands to be run during war"""
    def __init__(self, bot):
        self.bot = bot
        self.bot.coc_client.add_events(self.on_player_townhall_upgrade)
        self.guild = self.bot.get_guild(settings["discord"]["oakGuildId"])

    @commands.command()
    async def start_updates(self, ctx):
        await self.bot.coc_client.add_clan_update("#CVCJR89", member_updates=True)
        self.bot.coc_client.start_updates("all")
        await ctx.send("Updates started.")

    async def on_player_townhall_upgrade(self, old_th, new_th, player):
        conn = self.bot.db.pool
        coc_chat = self.bot.get_channel(settings["oakChannels"]["cocChat"])
        sql = "SELECT discord_id FROM rcs_discord_links WHERE player_tag = $1"
        row = await conn.fetchrow(sql, player.tag[1:])
        discord_id = row["discord_id"]
        user = await self.bot.get_user(discord_id)
        msg = f"Congratulations to <@{user.mention} on upgrading to Town Hall {new_th}!"
        await coc_chat.send(msg)
        old_role = await self.guild.get_role(settings["oakRoles"][f"TH{old_th}"])
        new_role = await self.guild.get_role(settings["oakRoles"][f"TH{new_th}"])
        await user.remove_roles(old_role, reason="Auto remove from TH upgrade event")
        await user.add_roles(new_role, reason="Auto assign from TH upgrade event")

    @commands.command(name="add_th_roles")
    async def add_roles(self, ctx):
        conn = self.bot.db.pool
        sql = "SELECT discord_ID, '#' || player_tag as player_tag FROM rcs_discord_links"
        rows = await conn.fetch(sql)
        for player in rows:



def setup(bot):
    bot.add_cog(ThRoles(bot))
