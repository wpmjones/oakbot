import coc
import discord
import re

from discord.ext import commands
from cogs.utils.constants import clans
from cogs.utils.converters import PlayerConverter
from cogs.utils.db import get_link_token, get_player_tag, get_discord_id
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


def base_display(base):
    return f"{base['map_position']}. {base['name']}{th_super(base['town_hall'])}"


def member_display(member):
    return f"{member.map_position}. {member.name}{th_super(member.town_hall)}"


def call_display(call, team):
    if team == "clan":
        return f"{call['caller_pos']}. {call['caller_name']}{th_super(call['caller_th'])}"
    else:   # team == "opponent"
        return f"{call['target_pos']}. {call['target_name']}{th_super(call['target_th'])}"


def expire_display(expiration):
    time_left = expiration - datetime.utcnow()
    hours, rem = divmod(time_left.total_seconds(), 3600)
    mins, secs = divmod(rem, 60)
    if hours == 0:
        return f"{int(mins):d}m"
    else:
        return f"{int(hours)}h {int(mins)}m"


class Timestamp:
    """Replicate similar functionality to coc.py timestamp
    Used for Phase 2 and 3"""

    def __init__(self, raw_time):
        self.raw_time = raw_time

    @property
    def time(self):
        return self.raw_time

    @property
    def now(self):
        return datetime.utcnow()

    @property
    def seconds_until(self):
        delta = self.time - self.now
        return delta.total_seconds()


class War(commands.Cog):
    """War bot commands and setup"""
    def __init__(self, bot):
        self.bot = bot
        self.bot.coc.add_events(self.on_war_attack)
        self.calls = []
        self.calls_by_attacker = {}
        self.calls_by_target = {}

    def cog_unload(self):
        self.bot.coc.remove_events(self.on_war_attack)

    @staticmethod
    def phase2(start_time):
        return Timestamp(start_time + timedelta(hours=9))

    @staticmethod
    def phase3(end_time):
        return Timestamp(end_time - timedelta(hours=6))

    async def get_war_id(self, prep_start_time):
        sql = "SELECT war_id FROM rcs_wars WHERE clan_tag = 'CVCJR89' AND prep_start_time = $1"
        fetch = await self.bot.pool.fetchrow(sql, prep_start_time)
        return fetch['war_id']

    async def init_calls(self, war):
        sql = ("SELECT call_id, caller_pos, target_pos, call_expiration, reserve, reserve_reason FROM oak_calls "
               "WHERE war_id = $1 AND call_expiration > $2 AND cancelled = False AND attack_complete = False "
               "ORDER BY target_pos")
        war_id = await self.get_war_id(war.preparation_start_time.time)
        fetch = await self.bot.pool.fetch(sql, war_id, datetime.utcnow())
        # clear calls for fresh reload
        self.calls = []
        self.calls_by_attacker = {}
        self.calls_by_target = {}
        for row in fetch:
            attacker = war.get_member_by(map_position=row['caller_pos'], is_opponent=False)
            defender = war.get_member_by(map_position=row['target_pos'], is_opponent=True)
            if defender:
                defender_name = defender.name
                defender_th = defender.town_hall
            else:
                defender_name = None
                defender_th = None
            call = {
                "call_id": row['call_id'],
                "caller_pos": row['caller_pos'],
                "caller_name": attacker.name,
                "caller_th": attacker.town_hall,
                "target_pos": row['target_pos'],
                "target_name": defender_name,
                "target_th": defender_th,
                "expires": row['call_expiration'],
                "reserve": row['reserve'],
                "reason": row['reserve_reason'],
            }
            self.calls.append(call)
            self.calls_by_attacker[row['caller_pos']] = call
            self.calls_by_target[row['target_pos']] = call

    async def get_base_owner(self, war, **kwargs):
        """Can pass in discord_id, player_tag, or map_ position
        All others will be ignored
        """
        if "discord_id" in kwargs.keys():
            base = {'discord_id': kwargs.get('discord_id')}
            print(base)
            api_response = get_player_tag(base['discord_id'])
            if api_response:
                print(api_response)
                if len(api_response) == 1:
                    base['player_tag'] = api_response[0]
                    member = war.get_member_by(tag=base['player_tag'])
                    if member:
                        base['name'] = member.name
                        base['map_position'] = member.map_position
                        base['town_hall'] = member.town_hall
                        base['attacks_left'] = 2 - len(member.attacks)
                        return base
                    else:
                        raise ValueError("This player is not in the current war.")
                else:
                    bases = []
                    for tag in api_response:
                        member = war.get_member_by(tag=tag)
                        print(member)
                        if member:
                            base['tag'] = member.tag
                            base['name'] = member.name,
                            base['map_position'] = member.map_position,
                            base['town_hall'] = member.town_hall,
                            base['attacks_left'] = 2 - len(member.attacks)
                            bases.append(base)
                    return bases
            else:
                # TODO change to elder channel or member status before going live
                channel = self.bot.get_channel(settings['oak_channels']['test_chat'])
                await channel.send(f"{kwargs.get('discord_id')} is missing from the links database. "
                                   f"Please run `/war add PlayerTag {kwargs.get('discord_id')}`.")
                raise ValueError(f"{kwargs.get('discord_id')} is missing from the links database. "
                                 f"Please run `/war add PlayerTag {kwargs.get('discord_id')}`.")
        elif "player_tag" in kwargs.keys():
            member = war.get_member_by(tag=kwargs.get('player_tag'))
            if member:
                base = {'tag': member.tag,
                        'name': member.name,
                        'discord_id': get_discord_id(member.tag),
                        'map_position': member.map_position,
                        'town_hall': member.town_hall,
                        'attacks_left': 2 - len(member.attacks)
                        }
                return base
            else:
                raise ValueError("This player is not in the current war.")
        elif "map_position" in kwargs.keys():
            base = {'map_position': int(kwargs.get('map_position'))}
            member = war.get_member_by(map_position=base['map_position'], is_opponent=False)
            base['name'] = member.name
            base['tag'] = member.tag
            base['discord_id'] = get_discord_id(member.tag)
            base['town_hall'] = member.town_hall
            base['attacks_left'] = 2 - len(member.attacks)
            return base
        else:
            raise ValueError("No valid keyword argument provided for this function.")

    async def add_call(self, war, caller, target):
        start_time = war.start_time.time
        now = datetime.utcnow()
        war_id = await self.get_war_id(war.preparation_start_time.time)
        sql = ("INSERT INTO oak_calls (war_id, caller_pos, target_pos, call_time, call_expiration)"
               "VALUES ($1, $2, $3, $4, $5)")
        await self.bot.pool.execute(sql, war_id, caller, target, now,
                                    now + timedelta(hours=3) if now > start_time else self.phase2(start_time).time)

    async def complete_call(self, call_id):
        sql = ("UPDATE oak_calls "
               "SET attack_complete = True "
               "WHERE call_id = $1")
        await self.bot.pool.execute(sql, call_id)

    async def cancel_call(self, call_id):
        sql = ("UPDATE oak_calls "
               "SET cancelled = True "
               "WHERE call_id = $1")
        await self.bot.pool.execute(sql, call_id)

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
        if pre == "":
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
        self.bot.logger.info(f"War Call Args: {args}\nLength: {len(args)}")
        war = await self.bot.coc.get_clan_war(clans['Reddit Oak'])
        if war.state not in ["preparation", "inWar"]:
            return await ctx.send("No active war")
        await self.init_calls(war)
        if len(args) == 2:
            # User provided calling base and target base
            caller_pos = int(args[0])
            target_pos = int(args[1])
            base_owner = await self.get_base_owner(war, map_position=caller_pos)
            self.bot.logger.info(f"Single base: {base_display(base_owner)} calling {target_pos}")
        elif len(args) == 1:
            # User provided only target base. Caller derived from Discord ID
            base_owner = await self.get_base_owner(war, discord_id=ctx.author.id)
            self.bot.logger.info(f"Base Owner: {base_owner}")
            if type(base_owner) is list:
                player_list = ""
                for player in base_owner:
                    player_list += f"{player['map_position']}. {player['name']}\n"
                resp = await ctx.prompt(f"You have multiple players in this war. Which base are you calling for?\n\n"
                                        f"{player_list}",
                                        additional_options=len(base_owner))
                base_owner = base_owner[resp - 1]
            target_pos = args[0]
            self.bot.logger.info(f"Multi base: {base_display(base_owner)} calling {target_pos}")
        else:
            return await ctx.send("I was expecting one or two numbers and that's not what I got. Care to try again?")
        # By this point, we should have a base_owner and a target_pos
        # Let's check to see if they are both valid
        if base_owner['map_position'] > war.team_size or target_pos > war.team_size:
            return await ctx.send(f"There are only {war.team_size} players in this war.")
        if not self.is_elder(ctx.author):
            if base_owner['discord_id'] != ctx.author.id:
                return await ctx.send(f"You are not allowed to call for {base_owner['name']} ({base_owner['tag']}.")
            for call in self.calls:
                if call['caller_pos'] == base_owner['map_position']:
                    if not call['reserve']:
                        return await ctx.send(f"{base_display(base_owner)} already called {call['target']}.")
                    else:
                        # If member has a reserve, cancel the remove and continue
                        await self.cancel_call(call['call_id'])
        if base_owner['attacks_left'] == 0:
            return await ctx.send(f"{base_display(base_owner)} has no more attacks left in this war.")
        for member in war.opponent.members:
            if member.map_position == target_pos:
                target = member  # for later use
                if member.best_opponent_attack and member.best_opponent_attack.stars == 3:
                    return await ctx.send(f"{target_pos}. {member.name} is already 3 starred.")
        for call in self.calls:
            if call['target_pos'] == target_pos:
                for member in war.opponent.members:
                    if member.map_position == target_pos:
                        return await ctx.send(f"{base_display(base_owner)} has already called "
                                              f"{member_display(member)}.")
        # Looks good, let's save it
        await self.add_call(war, base_owner['map_position'], target_pos)
        await ctx.send(f"{base_owner['map_position']}. {base_owner['name']} has called {target_pos}. {target.name}")

    @war.command(name="cancel")
    async def war_cancel(self, ctx, target_pos: int = None):
        """Cancel a call, based on the target, for the current war

        **Examples:**
        /war cancel 3
        """
        war = await self.bot.coc.get_clan_war(clans['Reddit Oak'])
        if war.state not in ["preparation", "inWar"]:
            return await ctx.send("No active war")
        if target_pos > war.team_size:
            return await ctx.send(f"There are only {war.team_size} players in this war.")
        await self.init_calls(war)
        if not target_pos:
            base_owner = await self.get_base_owner(war, discord_id=ctx.author.id)
            if len(base_owner) == 0:
                return await ctx.send("You have no bases in this war.")
            if type(base_owner) is list:
                player_list = ""
                for player in base_owner:
                    player_list += f"{player['map_position']}. {player['name']}\n"
                resp = await ctx.prompt(f"You have multiple players in this war. Which base are you calling for?\n\n"
                                        f"{player_list}",
                                        additional_options=len(base_owner))
                base_owner = base_owner[resp - 1]
            call = self.calls_by_attacker.get(base_owner['map_position'])
            if not call:
                return await ctx.send("I can't find any calls for you! Maybe try `/war cancel #` where # is the map "
                                      "position of the base to be attacked.")
        else:
            call = self.calls_by_target.get(target_pos)
            if not call:
                target = war.get_member_by(map_position=target_pos, is_opponent=True)
                return await ctx.send(f"No active call to cancel on {member_display(target)}.")
        # cancel the call
        await self.cancel_call(call['call_id'])
        # send response
        return await ctx.send(f"The call for {call_display(call, 'opponent')} has been cancelled.")

    @war.command(name="calls")
    async def war_calls(self, ctx):
        """Returns a list of all active calls for the current war"""
        war = await self.bot.coc.get_clan_war(clans['Reddit Oak'])
        if war.state not in ("preparation", "inWar"):
            return await ctx.send("No active war.")
        await self.init_calls(war)
        calls_by_defender = self.calls.copy()
        calls_by_defender.sort(key=lambda p: p['target_pos'])
        response = ["Calls"]
        for call in calls_by_defender:
            if call['reserve']:
                continue
            if call['expires'] == self.phase2(war.start_time.time).time:
                expires = "at end of phase 1"
            else:
                expires = f"in {expire_display(call['expires'])}"
            response.append(f"• {call_display(call, 'opponent')} called by {call_display(call, 'clan')} expires "
                            f"{expires}")
        if len(response) == 1:
            return await ctx.send("No active calls at this time.")
        else:
            return await ctx.send("\n".join(response))

    @war.command(name="open")
    async def war_open(self, ctx):
        """Returns any base that has not been 3 starred and does not have an active call"""
        war = await self.bot.coc.get_clan_war(clans['Reddit Oak'])
        if war.state not in ("preparation", "inWar"):
            return await ctx.send("No active war.")
        await self.init_calls(war)
        open_bases = ["Bases that are open"]
        targets = war.opponent.members.copy()
        targets.sort(key=lambda t: t.map_position)
        for target in targets:
            if target.best_opponent_attack:
                if target.best_opponent_attack.stars == 3 or target.map_position in self.calls_by_target:
                    continue
                open_bases.append(f"• {member_display(target)} - {target.best_opponent_attack.stars} stars "
                                  f"{int(target.best_opponent_attack.destruction)}%")
            else:
                open_bases.append(f"• {member_display(target)} - 0 stars")
        if len(open_bases) == 1:
            return await ctx.send("No open bases at this time.")
        else:
            return await ctx.send("\n".join(open_bases))

    @war.command(name="reserve")
    async def war_reserve(self, ctx, map_pos: int = None):
        """Mark map_position as reserve so that they don't get dinged for not attacks"""
        reasons = {
            1: "No good targets left",
            2: "Cannot attack at the beginning",
            3: "Waiting on others",
            4: "Waiting for heroes to wake up",
        }
        war = await self.bot.coc.get_clan_war(clans['Reddit Oak'])
        if war.state not in ("preparation", "inWar"):
            return await ctx.send("No active war.")
        await self.init_calls(war)
        if not map_pos:
            base_owner = await self.get_base_owner(war, discord_id=ctx.author.id)
        else:
            base_owner = await self.get_base_owner(war, map_position=map_pos)
            if not self.is_elder(ctx.author):
                if base_owner['discord_id'] != ctx.author.id:
                    return await ctx.send(f"You are not allowed to reserve for {base_owner['map_position']}. "
                                          f"{base_owner['name']}.")
        call = self.calls_by_attacker.get(base_owner['map_position'])
        if call:
            response = await ctx.prompt(f"You already have an active call on {call_display(call, 'clan')}. "
                                        f"Would you like to cancel it?")
            if response:
                await self.cancel_call(call['call_id'])
                await ctx.send("Existing call cancelled.  Now onto marking you reserve!")
            else:
                return await ctx.send("No action taken. Please cancel your active call before marking "
                                      "yourself reserve.")
        response = await ctx.prompt(f"Please select a reason:\n"
                                    f":one: {reasons[1]}\n"
                                    f":two: {reasons[2]}\n"
                                    f":three: {reasons[3]}\n"
                                    f":four: {reasons[4]}",
                                    additional_options=4)
        # Data looks good. Let's save it
        now = datetime.utcnow()
        sql = ("INSERT INTO oak_calls (war_id, caller_pos, call_time, call_expiration, reserve, reserve_reason) "
               "VALUES ($1, $2, $3, $4, True, $5)")
        await self.bot.pool.execute(sql,
                                    await self.get_war_id(war.preparation_start_time.time),
                                    base_owner['map_position'],
                                    now,
                                    self.phase3(war.end_time.time).time,
                                    reasons[response])
        await ctx.send(f"{base_display(base_owner)} has been marked as reserve.")

    @war.command(name="unreserve", hidden=True)
    async def war_unreserve(self, ctx, map_pos=None):
        """Remove reserve for the given map position"""
        war = await self.bot.coc.get_clan_war(clans['Reddit Oak'])
        if war.state not in ("preparation", "inWar"):
            return await ctx.send("No active war.")
        if not map_pos:
            base_owner = await self.get_base_owner(war, discord_id=ctx.author.id)
        else:
            base_owner = await self.get_base_owner(war, map_position=map_pos)
            if not self.is_elder(ctx.author):
                if base_owner['discord_id'] != ctx.author.id:
                    return await ctx.send(f"You are not allowed to reserve for {base_owner['map_position']}. "
                                          f"{base_owner['name']}.")
        # Data looks good. Get call reserve and remove it
        await self.init_calls(war)
        call = self.calls_by_attacker.get(base_owner['map_position'])
        if not call or not call['reserve']:
            return await ctx.send(f"{base_display(base_owner)} does not currently have a reserve call.")
        sql = "UPDATE oak_calls SET cancelled = True WHERE call_id = $1"
        await self.bot.pool.execute(sql, call['call_id'])
        await ctx.send(f"Reserve removed for {base_display(base_owner)}.")

    @war.command(name="add", hidden=True)
    async def war_add(self, ctx, player: PlayerConverter = None, member: discord.User = None):
        """Add player to links discord API so we can connect tags to Discord IDs"""
        if not self.is_elder(ctx.author):
            return await ctx.send("You are not authorized to use this command.")
        if not player:
            return await ctx.send("Please provide a valid in-game name or player tag.")
        if not member:
            return await ctx.send("Please provide a valid Disord ID or tag and ensure that this person is a "
                                  "member of the Reddit Oak Discord server.")
        # Add Discord ID to Oak Table
        url = f"{settings['google']['oak_table']}?call=add_discord&tag={player.tag[1:]}&discord_id={member.id}"
        async with self.bot.session.get(url) as r:
            if r.status >= 300:
                await ctx.send("There was a problem adding the Discord ID to the Oak Table. Please contact "
                               "<@251150854571163648>.")
        # Add link to Discord Links API
        token = get_link_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        url = "https://api.amazingspinach.com/links"
        payload = {"playerTag": player.tag, "discordId": str(member.id)}
        async with self.bot.session.post(url, json=payload, headers=headers) as r:
            if r.status >= 300:
                return await ctx.send(f"Error: {r.status} when adding for {player.name} ({player.tag}). "
                                      f"Please make sure they are properly linked.")
            else:
                resp = await r.text()
        await ctx.send(f"{resp}\n{player.name} ({player.tag}) has been successfully linked to {member.display_name}.")

    @war.command(name="status", aliases=["info"])
    async def war_status(self, ctx):
        """Provides information on the current war"""
        war = await self.bot.coc.get_current_war(clans['Reddit Oak'])
        if war.is_cwl:
            return await ctx.send("It appears that Reddit Oak is currently involved in the CWL.  Please use "
                                  "`/cwl` commands instead.")
        blank = emojis['other']['gap']
        th_list = (f"{emojis['th_icon'][13]} {emojis['th_icon'][12]} {emojis['th_icon'][11]} {emojis['th_icon'][10]} "
                   f"{emojis['th_icon'][9]}")
        # get war again with custom class
        war = await self.bot.coc.get_clan_war(clans['Reddit Oak'])
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
        elif now < self.phase2(war.start_time.time).time:
            time_calc = f"{to_time(self.phase2(war.start_time.time).seconds_until)} left in Phase 1!"
        elif now < self.phase3(war.end_time.time).time:
            time_calc = f"{to_time(self.phase3(war.end_time.time).seconds_until)} left in Phase 2!"
        else:
            if war.end_time.seconds_until > 0:
                time_calc = f"Free for all! War ends in {to_time(war.end_time.seconds_until)}"
            else:
                # Maybe maintenance pushed the end of war back some
                time_calc = f"Free for all! We're in overtime! War ends soon!"
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
        war = await self.bot.coc.get_clan_war(clans['Reddit Oak'])
        if war.state not in ["preparation", "inWar"]:
            now = datetime.utcnow()
            today = now.replace(hour=23, minute=0, second=0, microsecond=0)
            if today.weekday() > 1:
                next_war = today + timedelta((4 - today.weekday()) % 7)
            else:
                next_war = today + timedelta((1 - today.weekday()) % 7)
            time_calc = f"Next war expected in {to_time((next_war - now).total_seconds())}."
            return await ctx.send(f"There is no active war at this time, {ctx.author.display_name}.\n{time_calc}")
        await self.init_calls(war)
        # Get opted in info from rcs_war_members
        war_id = await self.get_war_id(war.preparation_start_time.time)
        sql = ("SELECT map_position, opted_in FROM rcs_war_members "
               "WHERE war_id = $1 AND is_opponent = False ORDER BY map_position")
        fetch = await self.bot.pool.fetch(sql, war_id)
        db_members = {}
        for row in fetch:
            db_members[row['map_position']] = row['opted_in']
        response = "Our lineup:\n"
        member_list = war.clan.members
        member_list.sort(key=lambda m: m.map_position)
        for member in member_list:
            new_line = f"• {member_display(member)}"
            new_line += [" - done", " - 1 attack left", " - 2 attacks left"][2 - len(member.attacks)]
            # Does the member have any calls
            try:
                call = self.calls_by_attacker[member.map_position]
                if not call['reserve']:
                    new_line += f" - called {call_display(call, 'opponent')}"
                else:
                    new_line += f" - reserve ({call['reason']})"
            except KeyError:
                # no call - skipping
                pass
            if db_members[member.map_position]:
                new_line += f" - opted in"
            response += new_line + "\n"
        return await ctx.send(response)

    @war.command(name="optin", aliases=["optedin"], hidden=True)
    async def war_optin(self, ctx, map_position: int = None):
        """Marks the specified base as opted in for this war (not required to attack)"""
        if not self.is_elder(ctx.author):
            return await ctx.send("You are not authorized to use this command.")
        if not map_position:
            return await ctx.send("You must provide a base number for this command.")
        war = await self.bot.coc.get_clan_war(clans['Reddit Oak'])
        if war.state not in ["preparation", "inWar"]:
            return await ctx.send("No active war")
        war_id = await self.get_war_id(war.preparation_start_time.time)
        member = war.get_member_by(map_position=map_position, is_opponent=False)
        sql = ("UPDATE rcs_war_members SET opted_in = NOT opted_in WHERE war_id = $1 AND is_opponent = False AND "
               "map_position = $2 "
               "RETURNING opted_in")
        opted_in = await self.bot.poll.execute(sql, war_id, map_position)
        if opted_in:
            return await ctx.send(f"{member_display(member)} marked as opted in.")
        else:
            return await ctx.send(f"Removed opted in for {member_display(member)}")

    @war.command(name="users", hidden=True)
    async def war_users(self, ctx):
        """Reports the links between discord and player tags"""
        if not self.is_elder(ctx.author):
            return await ctx.send("You are not authorized to use this command.")
        clan = await self.bot.coc.get_clan(clans['Reddit Oak'])
        yes_ids = ["Players with associated Discord users"]
        no_ids = ["Players without Discord users"]
        free = ["Discord users without associated players"]
        valid_ids = []
        print("Starting clan members")
        for member in clan.members:
            discord_id = get_discord_id(member.tag)
            if discord_id:
                yes_ids.append(f"• {member.name} ({member.tag}) is <@{discord_id}> ({discord_id})")
                valid_ids.append(discord_id)
            else:
                no_ids.append(f"• {member.name} ({member.tag})")
        print("Starting Discord users")
        guild = self.bot.get_guild(settings['discord']['oakguild_id'])
        for member in guild.members:
            if not member.bot and member.id not in valid_ids:
                free.append(f"• <@{member.id}> ({member.id})")
        response = (yes_ids + no_ids + free)
        await ctx.send_text(ctx.channel, response)

    @war.command(name="help")
    async def war_help(self, ctx):
        """Help for members and elders"""
        member_help = [
            u"• `/war status` - Get info about current war",
            u"• `/war open` - Find open bases",
            u"• `/war calls` - List active calls",
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

    @coc.WarEvents.war_attack(clans['Reddit Oak'])
    async def on_war_attack(self, attack, war):
        """Actions taken whenever a new attack happens
        Mark call completed
        Report to Discord
        """
        # TODO display differently if enemy is attacker
        await self.init_calls(war)
        call = self.calls_by_attacker.get(attack.attacker.map_position)
        if call:
            await self.complete_call(call['call_id'])
        war_channel = self.bot.get_channel(settings['oak_channels']['oak_war'])
        stars = ":star:" * attack.stars
        destruction = "" if attack.destruction == 3 else f"{int(attack.destruction)}%"
        await war_channel.send(f"{stars} {member_display(attack.attacker)} just attacked "
                               f"{member_display(attack.defender)} and got {attack.stars} stars "
                               f"{destruction}")

# marching orders
# tag attacks left
# end of war report to oak-war
# end of war report to elder-chat (missed attacks)


def setup(bot):
    bot.add_cog(War(bot))
