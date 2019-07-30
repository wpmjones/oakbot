import asyncio
import discord
from discord.ext import commands
from config import settings


class WarSetup(commands.Cog):
    """Commands to be run during war"""
    def __init__(self, bot):
        self.bot = bot
        self.coc = bot.coc_client
        self.coc.add_events(self.on_war_state_change)
        asyncio.ensure_future(self.coc.add_war_update("#CVCJR89"), loop=self.bot.loop)
        self.coc.start_updates("war")

    def cog_unload(self):
        self.coc.stop_updates("war")

    @property
    def elder_channel(self):
        return self.bot.get_channel(settings['oakChannels']['elder'])

    async def on_war_state_change(self, current_state, war):
        """ Assign inWar role to those participating in the current war """
        conn = self.bot.db.pool
        guild = self.bot.get_guild(settings['discord']['oakGuildId'])
        war_role = guild.get_role(settings['oakRoles']['inwar'])
        if war.state == "preparation":
            player_tags = [member.tag[1:] for member in war.members if not member.is_opponent]
            sql = (f"SELECT discord_ID, '#' || player_tag as player_tag "
                   f"FROM rcs_discord_links "
                   f"WHERE player_tag = ANY($1)")
            rows = await conn.fetch(sql, player_tags)
            names = []
            try:
                for row in rows:
                    is_user, user = is_discord_user(guild, int(row['discord_id']))
                    if not is_user:
                        self.bot.logger.error(f"Not a valid Discord ID\n"
                                              f"Player Tag: {row['player_tag']}\n"
                                              f"Discord ID: {row['discord_id']}\n")
                        continue
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
        elif war.state == "inWar":
            members = war_role.members
            if not members:
                player_tags = [member.tag[1:] for member in war.members if not member.is_opponent]
                sql = (f"SELECT discord_ID, '#' || player_tag as player_tag "
                       f"FROM rcs_discord_links "
                       f"WHERE player_tag = ANY($1)")
                rows = await conn.fetch(sql, player_tags)
                names = []
                try:
                    for row in rows:
                        is_user, user = is_discord_user(guild, int(row['discord_id']))
                        if not is_user:
                            self.bot.logger.error(f"Not a valid Discord ID\n"
                                                  f"Player Tag: {row['player_tag']}\n"
                                                  f"Discord ID: {row['discord_id']}\n")
                            continue
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


def is_discord_user(guild, discord_id):
    try:
        user = guild.get_member(discord_id)
        if user is None:
            return False, None
        else:
            return True, user
    except:
        return False, None


def setup(bot):
    bot.add_cog(WarSetup(bot))
