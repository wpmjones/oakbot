import coc
import discord

from discord.ext import commands
from cogs.war import to_time
from cogs.utils.constants import clans
from datetime import datetime
from config import settings, emojis


def breakdown(members, process=None):
    res = {}
    for m in members:
        th = m.town_hall if m.town_hall > 9 else 9
        if th not in res:
            res[th] = 0
        val = 1 if process is None else process(m)
        res[th] += val
    return "/".join(f"{res.get(th, 0)}" for th in range(13, 8, -1))


superscriptNumbers = u"⁰¹²³⁴⁵⁶⁷⁸⁹"


def sup(c):
    if ord('0') <= ord(c) <= ord('9'):
        return superscriptNumbers[ord(c) - ord('0')]
    else:
        return c


def th_super(s):
    s = str(s)
    ret = u""
    for c in s:
        ret += sup(c)
    return ret


def member_display(member):
    return f"{member.map_position}. {member.name}{th_super(member.town_hall)}"


class Cwl(commands.Cog):
    """War bot commands and setup"""
    def __init__(self, bot):
        self.bot = bot
        self.bot.coc.add_events(self.on_roster_change)

    def cog_unload(self):
        self.bot.coc.remove_events(self.on_roster_change)

    @commands.group(name="cwl", invoke_without_command=True)
    async def cwl(self, ctx, clan_name: str = "oak"):
        """CWL War Command
        Provides information on Clan War Leagues
        """
        if ctx.invoked_subcommand is not None:
            return

        if "oak" in clan_name.lower():
            clan_tag = clans['Reddit Oak']
        else:
            clan_tag = clans['Reddit Quercus']
        now = datetime.utcnow()
        war = await self.bot.coc.get_current_war(clan_tag)
        if not war.is_cwl:
            return await ctx.send(f"It appears that {war.clan} is not currently involved in CWL.  Please use "
                                  f"`/war` commands instead.")
        embed = discord.Embed(title="CWL Status", color=discord.Color.dark_blue())
        blank = emojis['other']['gap']
        group = await self.bot.coc.get_league_group(clan_tag)
        end_content = ""
        async for war in group.get_wars_for_clan(clan_tag):
            if war.state == "warEnded":
                prefix = war.status.title()
                end_content += (f"{prefix} - {war.clan} ({war.clan.stars}) vs "
                                f"{war.opponent} ({war.opponent.stars})\n")
            elif war.state == "inWar":
                # check for prior content and add embed if needed
                if end_content:
                    embed.add_field(name="Previous Rounds", value=end_content, inline=False)
                embed.add_field(name=f"{war.clan.name} vs {war.opponent.name}",
                                value=f"War ends in {to_time(war.end_time.seconds_until)}.",
                                inline=False)
                embed.add_field(name=war.clan.name,
                                value=f"{war.clan.stars} of {war.clan.max_stars} Stars\n"
                                      f"{war.clan.destruction:.1f}% Destruction",
                                inline=True)
                embed.add_field(name=war.opponent.name,
                                value=f"{war.opponent.stars} of {war.clan.max_stars} Stars\n"
                                      f"{war.opponent.destruction:.1f}% Destruction",
                                inline=True)
                embed.add_field(name=blank, value=blank, inline=True)
            elif war.state == "preparation":
                embed.add_field(name=f"Next Round vs {war.opponent.name}",
                                value=f"{breakdown(war.opponent.members)}\n"
                                      f"{to_time(war.start_time.seconds_until)} until war starts.")
        embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/clashofclans/images/9/97/LeagueMedal.png")
        await ctx.send(embed=embed)

    @cwl.command(name="roster")
    async def cwl_roster(self, ctx, clan_name: str = "oak"):
        """Responds with the upcoming enemy's roster so that you can plan your roster.

        **Example:**
        /cwl roster"""
        if "oak" in clan_name.lower():
            clan_tag = clans['Reddit Oak']
        else:
            clan_tag = clans['Reddit Quercus']
        war = await self.bot.coc.get_current_war(clan_tag, cwl_round=coc.WarRound.current_preparation)
        await ctx.send(f"**{war.opponent.name} Roster:**\n{breakdown(war.opponent.members)}")

    @coc.WarEvents.members(clans['Reddit Oak'])
    async def on_roster_change(self, old_war, new_war):
        self.bot.logger.info("Roster change detected in CWL")
        member_list = []
        for member in new_war.opponent.members:
            print(member_display(member))
            member_list.append(member_display(member))
        elder_channel = self.bot.get_channel(settings['oak_channels']['elder_chat'])
        old_breakdown = breakdown(old_war.members)
        new_breakdown = breakdown(new_war.members)
        content = (f"**CWL Roster Change**\n"
                   f"Old Breakdown: {old_breakdown}\n"
                   f"New Breakdown: {new_breakdown}")
        await elder_channel.send(content)
        await elder_channel.send("\n".join(member_list))


def setup(bot):
    bot.add_cog(Cwl(bot))
