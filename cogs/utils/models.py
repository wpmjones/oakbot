import coc

from datetime import datetime, timedelta
from cogs.utils.db import get_link_token
from config import settings


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


class WarData(coc.ClanWar):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bot = self._http.client.bot
        self.calls_by_target = {}
        self.calls_by_attacker = {}
        self.calls = []

    @property
    def phase2(self):
        return Timestamp(self.start_time.time + timedelta(hours=9))

    @property
    def phase3(self):
        return Timestamp(self.end_time.time - timedelta(hours=6))

    async def get_war_id(self, start_time):
        sql = "SELECT war_id FROM rcs_wars WHERE clan_tag = 'CVCJR89' AND start_time = $1"
        fetch = await self.bot.pool.fetchrow(sql, start_time)
        return fetch['war_id']

    async def get_call(self, map_position):
        sql = ("SELECT call_id, caller_pos, target_pos FROM oak_calls "
               "WHERE war_id = $1 AND call_expiration > $2 AND cancelled = False AND attack_complete = False "
               "AND caller_pos = $3")
        war_id = await self.get_war_id(self.preparation_start_time.time)
        fetch = await self.bot.pool.fetchrow(sql, war_id, datetime.utcnow(), map_position)
        return fetch['target_pos']

    async def init_calls(self):
        sql = ("SELECT call_id, caller_pos, target_pos, call_expiration, reserve, reserve_reason FROM oak_calls "
               "WHERE war_id = $1 AND call_expiration > $2 AND cancelled = False AND attack_complete = False "
               "ORDER BY target_pos")
        war_id = await self.get_war_id(self.preparation_start_time.time)
        fetch = await self.bot.pool.fetch(sql, war_id, datetime.utcnow())
        self.calls = []
        for row in fetch:
            attacker = self.get_member(map_position=row['caller_pos'], is_opponent=False)
            defender = self.get_member(map_position=row['target_pos'], is_opponent=True)
            call = {
                "call_id": row['call_id'],
                "caller_pos": row['caller_pos'],
                "caller_name": attacker.name,
                "caller_th": attacker.town_hall,
                "target_pos": row['target_pos'],
                "targer_name": defender.name,
                "target_th": defender.town_hall,
                "expires": row['call_expiration'],
                "reserve": row['reserve'],
                "reason": row['reserve_reason'],
            }
            self.calls.append(call)
            self.calls_by_attacker[row['caller_pos']] = call
            self.calls_by_target[row['target_pos']] = call

    async def get_open_bases(self):
        sql = ("SELECT call_id, caller_pos, target_pos FROM oak_calls "
               "WHERE war_id = $1 AND call_expiration > $2 AND cancelled = False AND attack_complete = False "
               "ORDER BY target_pos")
        war_id = await self.get_war_id(self.preparation_start_time.time)
        fetch = await self.bot.pool.fetch(sql, war_id, datetime.utcnow())
        called_bases = []
        for row in fetch:
            called_bases.append(fetch['target_pos'])
        open_bases = []
        for target in self.opponent.members:
            if target.map_position not in called_bases:
                # TODO add stars and % of best attack
                open_bases.append({
                    "map_position": target.map_position,
                    "name": target.name,
                    "town_hall": target.town_hall
                })
        return open_bases

    async def get_attacks_left(self, map_position):
        for member in self.clan.members:
            if member.map_position == map_position:
                attacks_left = {
                    "map_position": member.map_position,
                    "name": member.name,
                    "town_hall": member.town_hall,
                    "attacks_left": 2 - len(member.attacks)
                }
                return attacks_left
        else:
            raise ValueError(f"There are only {self.team_size} bases in this war.")

    async def get_discord_id(self, tag):
        """Get discord ID from player tag
        Returns single Discord ID because a player tag will only ever have one Discord ID"""
        token = get_link_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        async with self.bot.session as session:
            base_url = "https://api.amazingspinach.com/links/"
            url = base_url + tag
            async with session.get(url, headers=headers) as r:
                if r.status < 300:
                    data = await r.json()
                else:
                    raise ValueError(f"Links API Error: {r.status} when looking for {tag}. "
                                     f"Please make sure they are properly linked.")
        return data['discordId']

    async def get_player_tag(self, discord_id):
        """Get discord ID from player tag
        Returns json from response because there can be multiple tags per Discord ID"""
        token = get_link_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        async with self.bot.session as session:
            base_url = "https://api.amazingspinach.com/links/"
            url = base_url + discord_id
            async with session.get(url, headers=headers) as r:
                if r.status < 300:
                    data = await r.json()
                else:
                    raise ValueError(f"Links API Error: {r.status} when looking for {discord_id}. "
                                     f"Please make sure they are properly linked.")
        return data

    async def get_base_owner(self, **kwargs):
        """Can pass in discord_id, player_tag, or map_ position
        All others will be ignored
        """
        base = {}
        if "discord_id" in kwargs.keys():
            base['discord_id'] = kwargs.get('discord_id')
            api_response = await self.get_player_tag(base['discord_id'])
            if api_response:
                if len(api_response) == 1:
                    base['player_tag'] = api_response['playerTag']
                    for member in self.clan.members:
                        if member.tag == base['player_tag']:
                            base['name'] = member.name
                            base['map_position'] = member.map_position
                    else:
                        raise ValueError("This player is not in the current war.")
                else:
                    bases = []
                    for row in api_response:
                        base['player_tag'] = row['playerTag']
                        for member in self.clan.members:
                            if member.tag == base['player_tag']:
                                base['name'] = member.name
                                base['map_position'] = member.map_position
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
            base['tag'] = coc.utils.correct_tag(kwargs.get('player_tag'))
            for member in self.clan.members:
                if member.tag == base['tag']:
                    base['name'] = member.name
                    base['discord_id'] = await self.get_discord_id(member.tag)
                    base['map_position'] = member.map_position
                    break
            else:
                raise ValueError("This player is not in the current war.")
        elif "map_position" in kwargs.keys():
            base['map_position'] = kwargs.get('map_position')
            for member in self.clan.members:
                if member.map_position == base['map_position']:
                    base['name'] = member.name
                    base['tag'] = member.tag
                    base['discord_id'] = await self.get_discord_id(member.tag)
                    break
            else:
                raise ValueError("This player is not in the current war.")
        else:
            raise ValueError("No valid keyword argument provided for this function.")

    async def add(self, caller, target):
        """Add new call to database"""
        start_time = self.start_time.time
        now = datetime.utcnow()
        sql = ("INSERT INTO oak_calls (war_id, caller_pos, target_pos, call_time, call_expiration)"
               "VALUES ($1, $2, $3, $4, $5)")
        await self.bot.pool.execute(sql,
                                    await self.get_war_id(self.preparation_start_time.time),
                                    caller,
                                    target,
                                    now,
                                    now + timedelta(hours=3) if now > start_time else start_time + timedelta(hours=9))

    async def cancel(self, caller, target):
        """Removes call from database"""
        sql = ("UPDATE oak_calls"
               "SET cancelled = True"
               "WHERE war_id = $1 AND caller_pos = $2 AND target_pos = $3 AND cancelled = False")
        await self.bot.pool.execute(sql, await self.get_war_id(self.preparation_start_time.time), caller, target)


