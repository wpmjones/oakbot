import asyncio
import discord
from discord.ext import commands
from config import settings


class WarSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.war_roles())
        self.channel = self.bot.get_channel(settings['oakChannels']['testChat'])
        self.guild = self.bot.get_guild(settings['discord']['oakGuildId'])

    async def war_roles(self):
        """ Assign inWar role to those participating in the current war """
        await self.bot.wait_until_ready()
        conn = self.bot.db.pool
        sleep_time = 30
        war_state = ["notInWar", "warEnded"]
        while self == self.bot.get_cog("WarSetup"):
            await asyncio.sleep(sleep_time)
            war = await self.bot.coc_client.get_current_war("#CVCJR89")
            if war.state in war_state:
                continue
            if war.state in ["preparation", "inWar"]:
                war_role = self.guild.get_role(int(settings['oakRoles']['inwar']))
                player_tags = [member.tag[1:] for member in war.members if not member.is_opponent]
                sql = (f"SELECT discord_ID, '#' || player_tag as player_tag "
                       f"FROM rcs_discord_links "
                       f"WHERE player_tag = ANY($1)")
                rows = await conn.fetch(sql, player_tags)
                names = []
                try:
                    for row in rows:
                        is_user, user = is_discord_user(self.guild, int(row['discord_id']))
                        if not is_user:
                            self.bot.logger.error(f"Not a valid Discord ID\n"
                                                  f"Player Tag: {row['player_tag']}\n"
                                                  f"Discord ID: {row['discord_id']}\n")
                            continue
                        await user.add_roles(war_role, reason="Auto add role for war.")
                        names.append(user.display_name)
                    sleep_time = war.end_time.seconds_until + 900
                except:
                    self.bot.logger.exception("Add roles")
                try:
                    if names:
                        embed = discord.Embed(title="War roles added", color=discord.Color.red())
                        embed.add_field(name="Members in War", value="\n".join(names), inline=False)
                        await self.channel.send(embed=embed)
                        self.bot.logger.info("inWar role added automatically")
                    else:
                        self.bot.logger.warning("No players found in names list")
                except:
                    self.bot.logger.exception("Send Embed")
                war_state = ["preparation", "inWar"]
            else:
                # refresh role object, pull members with that role, remove the role
                war_role = self.guild.get_role(int(settings['oakRoles']['inwar']))
                members = war_role.members
                print(members)
                try:
                    for user in members:
                        await user.remove_roles(war_role, reason="Auto remove role after end of war.")
                except:
                    self.bot.logger.exception("War Roles")
                sleep_time = 900
                await self.channel.send("inWar roles removed for all players.")
                self.bot.logger.info("inWar role removed automatically")
                war_state = ["notInWar", "warEnded"]


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
