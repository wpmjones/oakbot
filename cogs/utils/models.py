import coc

from datetime import datetime, timedelta


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


