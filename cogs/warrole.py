import discord
from discord.ext import commands
from config import settings


class WarSetup(commands.Cog):
    """Commands to be run during war"""
    def __init__(self, bot):
        self.bot = bot
        self.bot.coc.add_war_update("#CVCJR89")
        self.bot.coc.add_events(self.on_war_state_change)
        self.bot.coc.start_updates("war")

    def cog_unload(self):
        self.bot.coc.stop_updates("war")

    @property
    def elder_channel(self):
        return self.bot.get_channel(settings['oakChannels']['elderChat'])

    async def on_war_state_change(self, current_state, war):
        """ Assign inWar role to those participating in the current war """
        self.bot.logger.debug(f"Current State: {current_state}\nWar State: {war.state}")
        conn = self.bot.db.pool
        guild = self.bot.get_guild(settings['discord']['oakGuildId'])
        war_role = guild.get_role(settings['oakRoles']['inwar'])
        if current_state == "preparation":
            self.bot.logger.debug("War state changed to preparation")
            player_tags = [member.tag[1:] for member in war.members if not member.is_opponent]
            sql = (f"SELECT discord_ID, '#' || player_tag as player_tag "
                   f"FROM rcs_discord_links "
                   f"WHERE player_tag = ANY($1)")
            rows = await conn.fetch(sql, player_tags)
            names = []
            try:
                for row in rows:
                    user = guild.get_member(int(row['discord_id']))
                    await user.add_roles(war_role, reason="Auto add role for war.")
                    names.append(user.display_name)
            except:
                self.bot.logger.exception("Failed while adding roles")
            try:
                if names:
                    embed = discord.Embed(title="War roles added", color=discord.Color.red())
                    embed.add_field(name="Members in War", value="\n".join(names), inline=False)
                    hours_left = war.end_time.seconds_until // 3600
                    minutes_left = (war.end_time.seconds_until - (hours_left*3600)) // 60
                    embed.set_footer(text=f"War ends in {hours_left} hours, {minutes_left} minutes.")
                    await self.elder_channel.send(embed=embed)
                    self.bot.logger.info("inWar role added automatically")
                else:
                    self.bot.logger.warning("No players found in names list")
            except:
                self.bot.logger.exception("Send Embed")
        elif current_state == "inWar":
            self.bot.logger.debug("War state changed to in war")
            # Remove all roles and re-add to compensate for missed prep
            members = war_role.members
            try:
                for user in members:
                    await user.remove_roles(war_role, reason="Auto remove role after end of war.")
            except:
                self.bot.logger.exception("War Roles")
            # Re-add roles for current war
            player_tags = [member.tag[1:] for member in war.members if not member.is_opponent]
            sql = (f"SELECT discord_ID, '#' || player_tag as player_tag "
                   f"FROM rcs_discord_links "
                   f"WHERE player_tag = ANY($1)")
            rows = await conn.fetch(sql, player_tags)
            names = []
            try:
                for row in rows:
                    user = guild.get_member(int(row['discord_id']))
                    await user.add_roles(war_role, reason="Auto add role for war.")
                    names.append(user.display_name)
            except:
                self.bot.logger.exception("Failed while adding roles")
            try:
                if names:
                    embed = discord.Embed(title="War roles added", color=discord.Color.red())
                    embed.add_field(name="Members in War", value="\n".join(names), inline=False)
                    hours_left = war.end_time.seconds_until // 3600
                    minutes_left = (war.end_time.seconds_until - (hours_left * 3600)) // 60
                    embed.set_footer(text=f"War ends in {hours_left} hours, {minutes_left} minutes.")
                    await self.elder_channel.send(embed=embed)
                    self.bot.logger.info("inWar role added automatically")
                else:
                    self.bot.logger.warning("No players found in names list")
            except:
                self.bot.logger.exception("Send Embed")
        else:
            # refresh role object, pull members with that role, remove the role
            members = war_role.members
            if members:
                try:
                    for user in members:
                        await user.remove_roles(war_role, reason="Auto remove role after end of war.")
                except:
                    self.bot.logger.exception("War Roles")
                await self.elder_channel.send("inWar roles removed for all players.")
                self.bot.logger.info("inWar role removed automatically")

    @commands.command(name="warroles", aliases=["warrole"], hidden=True)
    async def war_roles(self, ctx):
        """ Assign inWar role to those participating in the current war """
        guild = self.bot.get_guild(settings['discord']['oakGuildId'])
        conn = self.bot.db.pool
        war = await self.bot.coc.get_current_war("#CVCJR89")
        if war.state in ["preparation", "inWar"]:
            msg = await ctx.send("Adding roles. One moment...")
            war_role = guild.get_role(int(settings['oakRoles']['inwar']))
            player_tags = [member.tag[1:] for member in war.members if not member.is_opponent]
            sql = (f"SELECT discord_ID, '#' || player_tag as player_tag "
                   f"FROM rcs_discord_links "
                   f"WHERE player_tag = ANY($1)")
            rows = await conn.fetch(sql, player_tags)
            names = []
            try:
                for row in rows:
                    user = guild.get_member(int(row['discord_id']))
                    await user.add_roles(war_role, reason="Command - Add role for war.")
                    names.append(user.display_name)
            except:
                self.bot.logger.exception("Add roles")
            try:
                if names:
                    embed = discord.Embed(title="War roles added", color=discord.Color.red())
                    embed.add_field(name="Members in War", value="\n".join(names), inline=False)
                    hours_left = war.end_time.seconds_until // 3600
                    minutes_left = (war.end_time.seconds_until - (hours_left * 3600)) // 60
                    embed.set_footer(text=f"War ends in {hours_left} hours, {minutes_left} minutes.")
                    await msg.delete()
                    await ctx.send(embed=embed)
                    self.bot.logger.info("inWar role added via command")
                else:
                    self.bot.logger.warning("No players found in names list")
            except:
                self.bot.logger.exception("Send Embed")
        else:
            # refresh role object, pull members with that role, remove the role
            msg = await ctx.send("Removing war roles. One moment...")
            war_role = guild.get_role(int(settings['oakRoles']['inwar']))
            members = war_role.members
            try:
                for user in members:
                    await user.remove_roles(war_role, reason="Command - Remove role after end of war.")
            except:
                self.bot.logger.exception("War Roles")
            await msg.delete()
            await ctx.send("inWar roles removed for all players.")
            self.bot.logger.info("inWar role removed via command")


def setup(bot):
    bot.add_cog(WarSetup(bot))
