import discord
import re

from discord.ext import commands
from cogs.utils.converters import PlayerConverter
from cogs.utils.db import get_link_token
from cogs.utils.models import WarData
from datetime import datetime, timedelta
from config import settings, emojis


def to_time(seconds):
    d, r = divmod(seconds, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    if d > 0:
        return f"{d:.0f}d {h:.0f}h"
    elif h > 0:
        return f"{h:.0f}h {m:.0f}m"
    else:
        return f"{m:.0f}m"


def get_best_stars(member):
    if member.best_opponent_attack:
        return member.best_opponent_attack.stars
    else:
        return 0


def get_best_percentage(member):
    if member.best_opponent_attack:
        return member.best_opponent_attack.destruction
    else:
        return 0


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
    if ord('0') < ord(c) <= ord('9'):
        return superscriptNumbers[ord(c) - ord('0')]
    else:
        return c


def th_super(s):
    s = str(s)
    ret = u""
    for c in s:
        ret += sup(c)
    return ret


def caller_display(call):
    return f"{call['caller_pos']}. {call['caller_name']}{th_super(call['caller_th'])}"


def target_display(call):
    return f"{call['target_pos']}. {call['target_name']}{th_super(call['target_th'])}"


class War(commands.Cog):
    """War bot commands and setup"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="war", invoke_without_command=True)
    async def war(self, ctx, *args):
        """Main War Command
        Provides information on current war
        """
        if ctx.invoked_subcommand is not None:
            return

        if len(args) == 0:
            return await ctx.invoke(self.war_status)
        # Handle /war 3c5
        match = re.search(r"^(\d*)([cC]+)(\d*)$", args[0])
        if not match:
            return await ctx.send(f"Command {args[0]} not understood. Try `/war help`.")
        pre = match.group(1)
        post = match.group(3)
        if not pre:
            await ctx.invoke(self.war_call, post)
        else:
            await ctx.invoke(self.war_call, pre, post)

    @war.command(name="call", aliases=["c"])
    async def war_call(self, ctx, *args):
        """Call a target for the current war

        **Examples:**
        /war call 3
        /war c5
        /war 4c8 (for calling alts)
        """
        war = await self.bot.coc.get_clan_war('#CVCJR89', cls=WarData)
        await war.init_calls()
        if war.state not in ["preparation", "inWar"]:
            return await ctx.send("No active war")
        if len(args) == 2:
            # User provided calling base and target base
            caller_pos = int(args[0])
            target_pos = int(args[1])
            base_owner = await war.get_base_owner(map_position=caller_pos)
        elif len(args) == 1:
            # User provided only target base. Caller derived from Discord ID
            base_owner = await war.get_base_owner(discord_id=ctx.author.id)
            if type(base_owner) is list:
                player_list = ""
                for player in base_owner:
                    player_list += f"{player['map_position']}. {player['name']}\n"
                resp = await ctx.prompt(f"You have multiple players in this war. Which base are you calling for?\n\n"
                                        f"{player_list}",
                                        additional_options=len(base_owner))
                base_owner = base_owner[resp - 1]
            target_pos = args[0]
        else:
            return await ctx.send("I was expecting one or two numbers and that's not what I got. Care to try again?")
        # By this point, we should have a caller_pos and a target_pos
        # Let's check to see if they are both valid
        if base_owner['map_position'] > war.team_size or target_pos > war.team_size:
            return await ctx.send(f"There are only {war.team_size} players in this war.")
        if not self.is_elder(ctx.author):
            if base_owner['discord_id'] != ctx.author.id:
                return await ctx.send(f"You are not allowed to call for {base_owner['name']} ({base_owner['tag']}.")
        # TODO get this value somewhere else
        if war.get_attacks_left(base_owner['map_position']) == 0:
            return await ctx.send(f"{base_owner['name']} ({base_owner['tag']}) has no more attacks left in this war.")
        if not self.is_elder(ctx.author):
            for call in war.calls:
                if call['caller_pos'] == base_owner['map_position']:
                    return await ctx.send(f"{base_owner['name']} ({base_owner['tag']}) already called "
                                          f"{call['target']}.")
        for member in war.opponent.members:
            if member.map_position == target_pos:
                target = member  # for later use
                for attack in member.defenses:
                    if attack.stars == 3:
                        return await ctx.send(f"{target_pos}. {member.name} is already 3 starred.")
        for call in war.calls:
            if call['target_pos'] == target_pos:
                for member in war.opponent.members:
                    if member.map_position == target_pos:
                        return await ctx.send(f"{base_owner} has already called "
                                              f"{target_pos}. {member.name}.")
        # Looks good, let's save it
        await war.add(base_owner['map_position'], target_pos)
        await ctx.send(f"{base_owner['map_position']}. {base_owner['name']} has called {target_pos}. {target.name}")

    @war.command(name="cancel")
    async def war_cancel(self, ctx, target_pos=None):
        """Call a target for the current war

                **Examples:**
                /war call 3
                /war c5
                /war 4c8 (for calling alts)
                """
        war = await self.bot.coc.get_clan_war('#CVCJR89', cls=WarData)
        await war.init_calls()
        if war.state not in ["preparation", "inWar"]:
            return await ctx.send("No active war")
        call_owner = False
        if not target_pos:
            base_owner = await war.get_base_owner(discord_id=ctx.author.id)
            if type(base_owner) is list:
                player_list = ""
                for player in base_owner:
                    player_list += f"{player['map_position']}. {player['name']}\n"
                resp = await ctx.prompt(f"You have multiple players in this war. Which base are you calling for?\n\n"
                                        f"{player_list}",
                                        additional_options=len(base_owner))
                base_owner = base_owner[resp - 1]
            if war.calls_by_attacker[base_owner['map_position']]:
                target_pos = war.calls_by_attacker[base_owner['map_position']]['target_pos']
            else:
                return await ctx.send("I can't find any calls for that base!")
        # cancel the call

    @war.command(name="reserve", hidden=True)
    async def war_reserve(self, ctx, map_pos=None):
        """Mark map_position as reserve so that they don't get dinged for not attacks"""
        reasons = {
            1: "No good targets left",
            2: "Cannot attack at the beginning",
            3: "Waiting on others",
            4: "Waiting for heroes to wake up",
        }
        war = await self.bot.coc.get_clan_war('#CVCJR89', cls=WarData)
        if war.state not in ("preparation", "inWar"):
            return await ctx.send("No active war.")
        if not map_pos:
            base_owner = await war.get_base_owner(discord_id=ctx.author.id)
        else:
            base_owner = await war.get_base_owner(map_position=map_pos)
            if not self.is_elder(ctx.author):
                if base_owner['discord_id'] != ctx.author.id:
                    return await ctx.send(f"You are not allowed to reserve for {base_owner['map_position']}. "
                                          f"{base_owner['name']}.")
        resp = await ctx.prompt("Please select a reason:\n"
                                ":one: No good targets left"
                                ":two: Cannot attack at the beginning"
                                ":three: Waiting for others"
                                ":four: Waiting for heroes to wake up")
        # Data looks good. Let's save it
        conn = self.bot.pool
        sql = ("INSERT INTO oak_calls (war_id, caller_pos, reserve, reserve_reason) "
               "VALUES ($1, $2, $3, $4) "
               "ON CONFLICT (war_id, caller_pos, reserve) DO "
               "UPDATE SET reserve_reason = $4, cancelled = False "
               "WHERE war_ID = $1 AND caller_pos = $2 AND reserve = $3")
        await conn.execute(sql,
                           await war.get_war_id(war.preparation_start_time.time),
                           base_owner['map_position'],
                           True,
                           reasons[resp])
        await ctx.send(f"{base_owner['name']}. {base_owner['map_position']} has been marked as reserve.")

    @war.command(name="unreserve", hidden=True)
    async def war_unreserve(self, ctx, map_pos=None):
        """Remove reserve for the given map position"""
        war = await self.bot.coc.get_clan_war('#CVCJR89', cls=WarData)
        if war.state not in ("preparation", "inWar"):
            return await ctx.send("No active war.")
        if not map_pos:
            base_owner = await war.get_base_owner(discord_id=ctx.author.id)
        else:
            base_owner = await war.get_base_owner(map_position=map_pos)
            if not self.is_elder(ctx.author):
                if base_owner['discord_id'] != ctx.author.id:
                    return await ctx.send(f"You are not allowed to reserve for {base_owner['map_position']}. "
                                          f"{base_owner['name']}.")
        # Data looks good. Get call reserve and remove it
        await war.init_calls()
        try:
            call = war.calls_by_attacker[base_owner['map_position']]
        except KeyError:
            return await ctx.send(f"{base_owner['name']} does not currently have a reserve call.")
        conn = self.bot.pool
        sql = "UPDATE oak_calls SET cancelled = True WHERE call_id = $1"
        await conn.execute(sql, call['call_id'])
        await ctx.send(f"Reserve removed for {base_owner['name']}. {base_owner['map_position']}.")

    @war.command(name="add", hidden=True)
    async def war_add(self, ctx, player: PlayerConverter = None, member: discord.User = None):
        """Add player to links discord API so we can connect tags to Discord IDs"""
        if not player:
            return await ctx.send("Please provide a valid in-game name or player tag.")
        if not member:
            return await ctx.send("Please provide a valid Disord ID or tag and ensure that this person is a "
                                  "member of the Reddit Oak Discord server.")
        # Add Dsicord ID to Oak Table
        url = f"{settings['google']['oak_table']}?call=add_discord&tag={player.tag}&discord_id={member.id}"
        async with self.bot.session.get(url) as r:
            if r.status >= 300:
                await ctx.send("There was a problem adding the Discord ID to the Oak Table. Please contact "
                               "<@251150854571163648>.")
        # Add link to Discord L API
        token = get_link_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        url = "https://api.amazingspinach.com/links"
        payload = {"playerTag": player.tag, "discordId": str(member.id)}
        async with self.bot.session.post(url, json=payload, headers=headers) as r:
            if r.status >= 300:
                return await ctx.send(f"Error: {r.status} when adding for {player.name} ({player.tag}). "
                                      f"Please make sure they are properly linked.")
        await ctx.send(f"{player.name} ({player.tag}) has been successfully linked to {member.display_name}.")

    @war.command(name="status", aliases=["info"])
    async def war_status(self, ctx):
        """Provides information on the current war"""
        cwl_war = await self.bot.coc.get_league_war('#CVCJR89')
        if cwl_war.clan:
            return await ctx.send("It appears that Reddit Oak is currently involved in the CWL.  Please use "
                                  "`/cwl` commands instead.")
        blank = emojis['other']['gap']
        th_list = (f"{emojis['th_icon'][13]} {emojis['th_icon'][12]} {emojis['th_icon'][11]} {emojis['th_icon'][10]} "
                   f"{emojis['th_icon'][9]}")
        war = await self.bot.coc.get_clan_war('#CVCJR89', cls=WarData)
        now = datetime.utcnow()
        if war.state not in ["preparation", "inWar"]:
            today = now.replace(hour=23, minute=0, second=0, microsecond=0)
            if today.weekday() > 1:
                next_war = today + timedelta((4 - today.weekday()) % 7)
            else:
                next_war = today + timedelta((1 - today.weekday()) % 7)
            time_calc = f"War ended! Next war expected in {to_time((next_war - now).total_seconds())}."
        elif now < war.start_time.time:
            time_calc = f"Prep day. {to_time(war.start_time.seconds_until)} until war starts."
        elif now < war.phase2.time:
            time_calc = f"{to_time(war.phase2.seconds_until)} left in Phase 1!"
        elif now < war.phase3.time:
            time_calc = f"{to_time(war.phase3.seconds_until)} left in Phase 2!"
        else:
            time_calc = f"Free for all! War ends in {to_time(war.end_time.seconds_until)}"
        embed = discord.Embed(title="War Status", color=discord.Color.dark_blue())
        embed.set_thumbnail(url="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/160/microsoft/"
                                "106/crossed-swords_2694.png")
        embed.add_field(name=f"{war.clan.name} vs {war.opponent.name}", value=time_calc, inline=False)
        embed.add_field(name=war.clan.name,
                        value=(f"{war.clan.stars} of {war.clan.max_stars} Stars\n"
                               f"{war.clan.destruction:.1f}% Destruction"),
                        inline=True)
        embed.add_field(name=war.opponent.name,
                        value=(f"{war.opponent.stars} of {war.opponent.max_stars} Stars\n"
                               f"{war.opponent.destruction:.1f}% Destruction"),
                        inline=True)
        embed.add_field(name=blank, value=blank, inline=True)
        embed.add_field(name="Breakdown", value=breakdown(war.clan.members), inline=True)
        embed.add_field(name=th_list, value=breakdown(war.opponent.members), inline=True)
        embed.add_field(name=blank, value=blank, inline=True)
        embed.add_field(name="Attacks Left",
                        value=breakdown(war.clan.members, lambda m: 2 - len(m.attacks)),
                        inline=True)
        embed.add_field(name=":crossed_swords:",
                        value=breakdown(war.opponent.members, lambda m: 2 - len(m.attacks)),
                        inline=True)
        embed.add_field(name=blank, value=blank, inline=True)
        embed.add_field(name="Bases Standing",
                        value=breakdown(war.clan.members, lambda m: 1 if get_best_stars(m) < 3 else 0),
                        inline=True)
        embed.add_field(name=":shield:",
                        value=breakdown(war.opponent.members, lambda m: 1 if get_best_stars(m) < 3 else 0),
                        inline=True)
        embed.add_field(name=blank, value=blank, inline=True)
        await ctx.send(embed=embed)

    @war.command(name="lineup")
    async def war_lineup(self, ctx):
        """Returns Oak's lineup for the current war"""
        war = await self.bot.coc.get_clan_war('#CVCJR89', cls=WarData)
        if war.state not in ["preparation", "inWar"]:
            now = datetime.utcnow()
            today = now.replace(hour=23, minute=0, second=0, microsecond=0)
            if today.weekday() > 1:
                next_war = today + timedelta((4 - today.weekday()) % 7)
            else:
                next_war = today + timedelta((1 - today.weekday()) % 7)
            time_calc = f"Next war expected in {to_time((next_war - now).total_seconds())}."
            return await ctx.send(f"There is no active war at this time, {ctx.author.display_name}.\n{time_calc}")
        await war.init_calls()
        response = "Our lineup:\n"
        for member in war.clan.members:
            new_line = f"• {member.map_position}. {member.name}{th_super(member.town_hall)}"
            new_line += [" - done", " - 1 attack left", " - 2 attacks left"][2 - len(member.attacks)]
            # Does the member have any calls
            try:
                call = war.calls_by_attacker[member.map_position]
                if not call['reserve']:
                    new_line += f" - called {target_display(war.calls_by_attacker[member.map_position])}"
                else:
                    new_line += f" - reserve ({call['reason']})"
            except KeyError:
                # no call - skipping
                pass
            # TODO add opted in info once prepped
            response += new_line + "\n"
        return await ctx.send(response)

    @war.command(name="help")
    async def war_help(self, ctx):
        """Help for members and elders"""
        member_help = [
            u"• `/war status` - Get info about current war",
            u"• `/war open` - Find open bases",
            u"• `/war calls` - List active calls",
            u"• `/war sheet` - Get link to Clan War Sheet",
            u"• `/war call <pos>` - Call a target in war",
            u"• `/war c5` - Call a target in war",
            u"• `/war 3c5` - Call target specifying caller (for alts)",
            u"• `/war cancel <target>` - Cancel your active call (target needed only for alts)",
            u"• `/war reserve <pos>` - Sign up as reserve (no targets in my range) (pos needed only for alts)",
            u"• `/war lineup` - Show our lineup with available attacks",
            u"• `/war march` - Show marching orders for our lineup",
        ]
        elder_help = [
            u"• `/war optedin <pos>` - mark player as opted in (or reset the marking if already set)",
            u"• `/war enemy <enemystars>` - set enemy stars (if automatic recording is not working)",
            u"• `/war 3a5 <stars> <percentage>` - record attack (if automatic recording is not working)",
            u"• `/war 3c5` - call target by position, multiple calls can be made by elders for one attacker",
            u"• `/war cancel <pos>` - cancel current call on target",
            u"• `/war reserve <pos>` - mark member at pos as reserve",
            u"• `/war unreserve <pos>` - remove mark-as-reserve from member",
            u"• `/war order <posrange> order text` - issue order for base or range of bases",
            u"• `/war tag <posrange> tag text` - tag members with at least one attack left",
            u"• `/war difficult_bases` - show opponent bases with many defenses",
            u"• `/war add <player> <slacktag>` - add player to slack user",
            u"• `/war remove <player> <slacktag>` - remove player from slack user",
            u"• `/war users` - list current associations",
            u"• `/war skip <clan|opponent> <posrange>` - mark player as skipped (for CWL)",
            u"• `/war skipped <clan|opponent>` - show players marked as skipped",
        ]
        if self.is_elder(ctx.author) and ctx.channel.id not in (settings['oak_channels']['general'],
                                                                settings['oak_channels']['coc_chat'],
                                                                settings['oak_channels']['oak_war']):
            await ctx.send("\n".join(["**Help**"] + member_help + ["**Elder only:**"] + elder_help))
        else:
            await ctx.send("\n".join(["**Help**"] + member_help))

    @staticmethod
    def is_elder(author):
        """Checks to see if the caller is an elder or higher"""
        # Tuba gets to do this too
        if author.id == 251150854571163648:
            return True
        # Check everyone else
        elder_roles = [settings['oak_roles']['elder'],
                       settings['oak_roles']['co-leader'],
                       settings['oak_roles']['leader']]
        check = [x.id for x in author.roles if x.id in elder_roles]
        if check:
            return True
        else:
            return False


# cancel
# Open
# optedin
# lineup
# marching orders
# Skip
# unskip
# skipped
# tag attacks left

def setup(bot):
    bot.add_cog(War(bot))
