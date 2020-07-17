import coc
import discord
import asyncio

from discord.ext import commands
from cogs.utils.db import get_discord_id
from cogs.utils.constants import clans
from cogs.war import member_display
from config import settings


class WarSetup(commands.Cog):
    """Commands to be run during war"""
    def __init__(self, bot):
        self.bot = bot
        self.elder_channel = None
        self.guild = None
        self.bot.coc.add_events(self.on_war_state_change)

    def cog_unload(self):
        self.bot.coc.remove_events(self.on_war_state_change)

    @coc.WarEvents.state(clans['Reddit Oak'])
    async def on_war_state_change(self, old_war, new_war):
        """ Assign inWar role to those participating in the current war """
        if not self.guild:
            self.guild = self.bot.get_guild(settings['discord']['oakguild_id'])
        test_chat = self.bot.get_channel(364507837550034956)
        war_chat = self.bot.get_channel(settings['oak_channels']['oak_war'])
        war_role = self.guild.get_role(settings['oak_roles']['inwar'])
        if not self.elder_channel:
            self.elder_channel = self.bot.get_channel(settings['oak_channels']['elder_chat'])
        if new_war.state == "preparation":
            await test_chat.send(f"{new_war.clan.name} is in preparation")
            names = []
            war = await self.bot.coc.get_current_war("#CVCJR89")
            for member in war.members:
                if member.is_opponent:
                    continue
                discord_id = get_discord_id(member.tag)
                user = self.guild.get_member(discord_id)
                await user.add_roles(war_role, reason="Auto add role for war.")
                names.append(user.display_name)
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
        elif new_war.state == "warEnded":
            # pull members with war role, remove the role
            members = war_role.members
            if members:
                try:
                    for user in members:
                        await user.remove_roles(war_role, reason="Auto remove role after end of war.")
                except:
                    self.bot.logger.exception("War Role Removal")
                await self.elder_channel.send("inWar roles removed for all players.")
                self.bot.logger.info("inWar role removed automatically")
            # send after war reports to oak-war
            results_text = {"won": "are victorious!",
                            "lost": "lost",
                            "tie": "tied! We actually tied!"
                            }[new_war.status]
            color = {"won": discord.Color.green(), "lost": discord.Color.red(), "tie": discord.Color.gold()}[
                new_war.status]
            defenses = sorted((m for m in new_war.clan.members if m.defense_count >= 2),
                              key=lambda m: m.defense_count,
                              reverse=True)
            formatted_def = ["{} {} ({} defs)".format(member_display(member),
                                                      ':shield:' * member.defense_count,
                                                      member.defense_count) for member in defenses]
            sixers = []
            for member in new_war.clan.members:
                if member.star_count == 6:
                    sixers.append(member)
            sixers = sorted((member for member in sixers), key=lambda m: m.map_position)
            embed = discord.Embed(color=color, title=f"War is over and we {results_text}!")
            embed.set_thumbnail(url=f"http://www.mayodev.com/images/{new_war.status}.png")
            embed.add_field(name="Reddit Oak",
                            value=f"{new_war.clan.stars} Stars\nDestruction: {new_war.clan.destruction:.1f}%",
                            inline=True)
            embed.add_field(name=new_war.opponent.name,
                            value=f"{new_war.opponent.stars} Stars\nDestruction: {new_war.opponent.destruction:.1f}%",
                            inline=True)
            embed.add_field(name="Sixers",
                            value="\n".join("{} :fire:".format(member_display(m)) for m in sixers),
                            inline=False)
            embed.add_field(name="Defenses",
                            value="\n".join(formatted_def) if len(
                                formatted_def) else "No one had more than 2 defenses.",
                            inline=False)
            await war_chat.send(embed=embed)
            # send missed attacks report to elder channel
            sql = "SELECT war_id FROM rcs_wars WHERE clan_tag = 'CVCJR89' AND prep_start_time = $1"
            war_id = await self.bot.pool.fetchval(sql, new_war.preparation_start_time.time)
            sql = "SELECT tag FROM rcs_war_members WHERE war_id = $1 AND is_opponent is False AND opted_in is False"
            fetch = await self.bot.pool.fetch(sql, war_id)
            misses = []
            for row in fetch:
                member = new_war.get_member(f"#{row[0]}")
                if member and len(member.attacks) < 2:
                    misses.append(member)
            misses.sort(key=lambda m: m.map_position)
            embed = discord.Embed(name="Elder war summary")
            embed.add_field(name="Missed attacks",
                            value="\n".join("{} missed {}".format(member_display(m),
                                                                  "1 attack" if len(m.attacks) == 1 else "2 attacks")
                                            for m in misses)
                            if len(misses) else "No missed attacks this war")
            await self.elder_channel.send(embed=embed)
        else:  # inWar
            await test_chat.send(f"{new_war.clan.name} is in war")

    @commands.command(name="end1", hidden=True)
    async def war_end1(self, ctx):
        new_war = await self.bot.coc.get_clan_war(clans['Reddit Oak'])
        war_chat = self.bot.get_channel(settings['oak_channels']['oak_war'])
        results_text = {"won": "are victorious!",
                        "lost": "lost",
                        "tie": "tied! We actually tied!"
                        }[new_war.status]
        color = {"won": discord.Color.green(), "lost": discord.Color.red(), "tie": discord.Color.gold()}[new_war.status]
        defenses = sorted((m for m in new_war.clan.members if m.defense_count >= 2),
                          key=lambda m: m.defense_count,
                          reverse=True)
        formatted_def = ["{} {} ({} defs)".format(member_display(member),
                                                  ':shield:' * member.defense_count,
                                                  member.defense_count) for member in defenses]
        sixers = []
        for member in new_war.clan.members:
            if member.star_count == 6:
                sixers.append(member)
        sixers = sorted((member for member in sixers), key=lambda m: m.map_position)
        embed = discord.Embed(color=color, title=f"War is over and we {results_text}!")
        embed.set_thumbnail(url=f"http://www.mayodev.com/images/{new_war.status}.png")
        embed.add_field(name="Reddit Oak",
                        value=f"{new_war.clan.stars} Stars\nDestruction: {new_war.clan.destruction:.1f}%",
                        inline=True)
        embed.add_field(name=new_war.opponent.name,
                        value=f"{new_war.opponent.stars} Stars\nDestruction: {new_war.opponent.destruction:.1f}%",
                        inline=True)
        embed.add_field(name="Sixers",
                        value="\n".join("{} :fire:".format(member_display(m)) for m in sixers),
                        inline=False)
        embed.add_field(name="Defenses",
                        value="\n".join(formatted_def) if len(formatted_def) else "No one had more than 2 defenses.",
                        inline=False)
        await war_chat.send(embed=embed)

    @commands.command(name="end2", hidden=True)
    async def war_end2(self, ctx):
        new_war = await self.bot.coc.get_clan_war(clans['Reddit Oak'])
        if not self.elder_channel:
            self.elder_channel = self.bot.get_channel(settings['oak_channels']['elder_chat'])
        sql = "SELECT war_id FROM rcs_wars WHERE clan_tag = 'CVCJR89' AND prep_start_time = $1"
        war_id = await self.bot.pool.fetchval(sql, new_war.preparation_start_time.time)
        sql = "SELECT tag FROM rcs_war_members WHERE war_id = $1 AND is_opponent is False AND opted_in is False"
        fetch = await self.bot.pool.fetch(sql, war_id)
        misses = []
        for row in fetch:
            member = new_war.get_member(f"#{row[0]}")
            if member and len(member.attacks) < 2:
                misses.append(member)
        misses.sort(key=lambda m: m.map_position)
        embed = discord.Embed(name="Elder war summary")
        embed.add_field(name="Missed attacks",
                        value="\n".join("{} missed {}".format(member_display(m),
                            "1 attack" if len(m.attacks) == 1 else "2 attacks") for m in misses)
                            if len(misses) else "No missed attacks this war")
        await self.elder_channel.send(embed=embed)

    @commands.command(name="warroles", aliases=["warrole"], hidden=True)
    async def war_roles(self, ctx):
        """ Assign inWar role to those participating in the current war """
        guild = self.bot.get_guild(settings['discord']['oakguild_id'])
        conn = self.bot.pool
        war = await self.bot.coc.get_current_war("#CVCJR89")
        if war.state in ["preparation", "inWar"]:
            msg = await ctx.send("Adding roles. One moment...")
            war_role = guild.get_role(int(settings['oak_roles']['inwar']))
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
            war_role = guild.get_role(int(settings['oak_roles']['inwar']))
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
