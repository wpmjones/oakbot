import discord
import asyncio
from discord.ext import commands
from config import settings


class WarSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.change_flag = 0

    async def war_roles(self):
        """ Assign inWar role to those participating in the current war """
        await self.bot.wait_until_ready()
        conn = self.bot.db.pool
        channel = self.bot.get_channel(settings['oakChannels']['testChat'])
        guild = self.bot.get_guild(settings['discord']['oakGuildId'])
        war_role = guild.get_role(int(settings['oakRoles']['inwar']))
        while self == self.bot.get_cog("WarSetup"):
            try:
                war = await self.bot.coc_client.get_current_war("#CVCJR89")
                if war.state in ["preparation", "inWar"] and self.change_flag == 0:
                    # find members in current war and assign role
                    player_tags = [member.tag[1:] for member in war.members if not member.is_opponent]
                    sql = (f"SELECT discord_ID, '#' || player_tag as player_tag "
                           f"FROM rcs_discord_links "
                           f"WHERE player_tag = ANY($1)")
                    rows = await conn.fetch(sql, player_tags)
                    names = []
                    for row in rows:
                        is_user, user = is_discord_user(guild, int(row['discord_id']))
                        if not is_user:
                            self.bot.logger.error(f"Not a valid Discord ID\n"
                                                  f"Player Tag: {row['player_tag']}\n"
                                                  f"Discord ID: {row['discord_id']}\n")
                            continue
                        await user.add_roles(war_role, reason="Auto add role for war.")
                        names.append(user.display_name)
                    sleep_time = war.end_time.seconds_until
                    if names:
                        embed = discord.Embed(title="War roles added", color=discord.Color.red())
                        embed.add_field(name="Members in War", value="\n".join(names), inline=False)
                        await channel.send(embed=embed)
                        # change_flag tells the function that roles have already been assigned
                        change_flag = 1
                        self.bot.logger.info("inWar role added automatically")
                    else:
                        self.bot.logger.warning("No players found in names list")
                elif war.state in ["warEnded", "notInWar"] and self.change_flag == 1:
                    sql = (f"SELECT discord_ID, '#' || player_tag as player_tag "
                           f"FROM rcs_discord_links")
                    rows = await conn.fetch(sql)
                    for row in rows:
                        is_user, user = is_discord_user(guild, int(row['discord_id']))
                        if not is_user:
                            self.bot.logger.error(f"Not a valid Discord ID\n"
                                                  f"Player Tag: {row['player_tag']}\n"
                                                  f"Discord ID: {row['discord_id']}\n")
                            pass
                        await user.remove_roles(war_role, reason="Auto remove role after end of war.")
                    sleep_time = 900
                    self.change_flag = 0
                    await channel.send("inWar roles removed for all players.")
                    self.bot.logger.info("inWar role removed automatically")
                else:
                    sleep_time = 900
                await asyncio.sleep(sleep_time)
            except:
                self.bot.logger.exception("War Roles")


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
    c = WarSetup(bot)
    bot.add_cog(c)
    bot.loop.create_task(c.war_roles())
