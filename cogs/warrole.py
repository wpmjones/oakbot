import coc
import discord

from discord.ext import commands
from cogs.utils.db import get_discord_id
from config import settings


tag_list = ['#8J8QJ2LV', '#8JL9QP8Y', '#JQCR9JGY', '#2LGPJYVJ', '#9RVVPG2J', '#2PYVUPV8', '#UUJ28VY', '#8GUY820R',
            '#CVCJR89', '#9RCRVL8V', '#YPCCUR8', '#2C8JV0PG', '#22J8ULLL', '#2Y28CGP8', '#JYVRY0L', '#C0LCCU8',
            '#Q2PP8VY', '#G88CYQP', '#82U2UVU9', '#2CVLP0P0', '#29PVJU2R', '#2UUCUJL', '#VPVPC080', '#CU8YQYCG',
            '#8V8UU9V', '#UVU80LC9', '#LY2UJ02C', '#UPVV99V', '#P9UUJLV', '#GVJ2RQC', '#9RPU22RU', '#YU88PCR',
            '#98QR9LJJ', '#8YYRVUYC', '#8UL9CCY2', '#2JU0P82U', '#8QGLJGJR', '#22GLCR9Q', '#2UGVGR2J', '#PJUQVRC',
            '#888GPQ0J', '#88UUCRR9', '#202GG92Q', '#2922CY2R', '#UGJPVJR', '#GJ9PJYCV', '#2YL0GYC0', '#2Y09LV28',
            '#RRJ0JUC', '#90V2UGJQ', '#9Q9V8YLJ', '#29Q9809', '#RLLVJ00J', '#99VL0Y9R', '#9L2PRL0U', '#22CGCR88C',
            '#R8LU8QRQ', '#RUJYCVL', '#20CCR22U', '#29QLY92Y2', '#29YL2J9C0', '#2JUJ2G22', '#902PQVRL', '#9P098JRQ',
            '#8PQGQC8', '#PPYRJ00P', '#PL90YR', '#29U8JLJL', '#20RP90PLL', '#UV2RU9GJ', '#LQRPQ2Q2']


class WarSetup(commands.Cog):
    """Commands to be run during war"""
    def __init__(self, bot):
        self.bot = bot
        self.elder_channel = None
        self.guild = None
        bot.loop.create_task(self.cog_init_ready())

    async def cog_init_ready(self):
        """Sets variables properly"""
        await self.bot.wait_until_ready()
        if not self.guild:
            self.guild = self.bot.get_guild(settings['discord']['oakguild_id'])
        if not self.elder_channel:
            self.elder_channel = self.bot.get_channel(settings['oak_channels']['elder_chat'])

    @coc.WarEvents.state(tags=tag_list)
    async def on_war_state_change(self, old_war, new_war):
        """ Assign inWar role to those participating in the current war """
        if not self.guild:
            self.guild = self.bot.get_guild(settings['discord']['oakguild_id'])
        test_chat = self.bot.get_channel(364507837550034956)
        war_role = self.guild.get_role(settings['oak_roles']['inwar'])
        if new_war.state == "preparation":
            self.bot.logger.debug("War state changed to preparation")
            await test_chat.send(f"{new_war.clan.name} is in preparation")
            # names = []
            # war = await self.bot.coc.get_current_war("#CVCJR89")
            # for member in war.members:
            #     if member.is_opponent:
            #         continue
            #     discord_id = get_discord_id(member.tag)
            #     user = self.guild.get_member(discord_id)
            #     await user.add_roles(war_role, reason="Auto add role for war.")
            #     names.append(user.display_name)
            # try:
            #     if names:
            #         embed = discord.Embed(title="War roles added", color=discord.Color.red())
            #         embed.add_field(name="Members in War", value="\n".join(names), inline=False)
            #         hours_left = war.end_time.seconds_until // 3600
            #         minutes_left = (war.end_time.seconds_until - (hours_left*3600)) // 60
            #         embed.set_footer(text=f"War ends in {hours_left} hours, {minutes_left} minutes.")
            #         await self.elder_channel.send(embed=embed)
            #         self.bot.logger.info("inWar role added automatically")
            #     else:
            #         self.bot.logger.warning("No players found in names list")
            # except:
            #     self.bot.logger.exception("Send Embed")
        elif new_war.state in ("warEnded", "notInWar"):
            await test_chat.send(f"{new_war.clan.name} is in {new_war.state}")
            # refresh role object, pull members with that role, remove the role
            # members = war_role.members
            # if members:
            #     try:
            #         for user in members:
            #             await user.remove_roles(war_role, reason="Auto remove role after end of war.")
            #     except:
            #         self.bot.logger.exception("War Role Removal")
            #     await self.elder_channel.send("inWar roles removed for all players.")
            #     self.bot.logger.info("inWar role removed automatically")
        else:
            await test_chat.send(f"{new_war.clan.name} is in war")

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
