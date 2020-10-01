import gspread
import json
import pyodbc
import requests
import sys

from discord.ext import commands, tasks
from cogs.utils.constants import clans
from datetime import datetime
from config import settings


class Background(commands.Cog):
    """Cog for background tasks. No real commands here."""
    def __init__(self, bot):
        self.bot = bot
        self.guild = None
        self.check_quercus.start()
        self.check_oak.start()
        self.oak_data_push.start()

    def cog_unload(self):
        self.check_quercus.cancel()
        self.check_oak.cancel()
        self.oak_data_push.cancel()

    async def cog_init_ready(self) -> None:
        """Sets the guild properly"""
        await self.bot.wait_until_ready()
        if not self.guild:
            self.guild = self.bot.get_guild(settings['discord']['oakguild_id'])

    @tasks.loop(hours=1.0)
    async def oak_data_push(self):
        """Update SQL database with latest info from API"""
        # Class for items with a level of 0
        class NullItem:
            level = 0
            value = 0

        now = datetime.utcnow()
        driver = "ODBC Driver 17 for SQL Server"
        conn = pyodbc.connect(f"DRIVER={driver};SERVER={settings['database']['server']};"
                              f"DATABASE={settings['database']['database']};UID={settings['database']['username']};"
                              f"PWD={settings['database']['password']}")
        cursor = conn.cursor()
        clan = await self.bot.coc.get_clan(clans['Reddit Oak'])
        sql1 = ("INSERT INTO coc_oak (tag, playerName, XPLevel, trophies, donations, donReceived, league, "
                "leagueIcon, thLevel, warStars, attackWins, defenseWins, bestTrophies, vsTrophies, bestVsTrophies, "
                "versusBattleWins, builderHall, timestamp) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)")
        sql2 = ("UPDATE coc_oak "
                "SET barbKing = ?, archQueen = ?, grandWarden = ?, royalChamp = ?, battleMachine = ?, "
                "clanGames = ?, wallWrecker = ?, battleBlimp = ?, stoneSlammer = ?, siegeBarracks = ? "
                "WHERE tag = ? AND timestamp = ?")
        self.bot.logger.info("Starting member loop for SQL")
        to_google = []
        async for m in clan.get_detailed_members():
            print(m.name)
            clan_games = m.get_achievement("Games Champion").value if m.get_achievement("Games Champion") else 0
            barb_king = m.get_hero("Barbarian King").level if m.get_hero("Barbarian King") else 0
            arch_queen = m.get_hero("Archer Queen").level if m.get_hero("Archer Queen") else 0
            grand_warden = m.get_hero("Grand Warden").level if m.get_hero("Grand Warden") else 0
            royal_champ = m.get_hero("Royal Champion").level if m.get_hero("Royal Champion") else 0
            battle_mach = m.get_hero("Battle Machine").level if m.get_hero("Battle Machine") else 0
            wall_wrecker = m.siege_machines[0].level if len(m.siege_machines) > 0 else 0
            battle_blimp = m.siege_machines[1].level if len(m.siege_machines) > 1 else 0
            stone_slammer = m.siege_machines[2].level if len(m.siege_machines) > 2 else 0
            barracks = m.siege_machines[3].level if len(m.siege_machines) > 3 else 0
            cursor.execute(sql1, m.tag[1:], m.name, m.exp_level, m.trophies, m.donations, m.received,
                           m.league.name, m.league.icon.url, m.town_hall, m.war_stars, m.attack_wins,
                           m.defense_wins, m.best_trophies, m.versus_trophies, m.best_versus_trophies,
                           m.versus_attack_wins, m.builder_hall, now)
            conn.commit()
            cursor.execute(sql2, barb_king, arch_queen, grand_warden, royal_champ, battle_mach, clan_games,
                           wall_wrecker, battle_blimp, stone_slammer, barracks, m.tag[1:], now)
            conn.commit()
            # Prep dict for Google
            to_google.append({"tag": m.tag, "townHall": m.town_hall, "warStars": m.war_stars,
                              "attackWins": m.attack_wins, "defenseWins": m.defense_wins,
                              "bestTrophies": m.best_trophies, "barbKing": barb_king,
                              "archQueen": arch_queen, "grandWarden": grand_warden, "batMach": battle_mach,
                              "builderHallLevel": m.builder_hall, "versusTrophies": m.versus_trophies,
                              "bestVersusTrophies": m.best_versus_trophies, "versusBattleWins": m.versus_attack_wins,
                              "clanGames": clan_games, "name": m.name, "expLevel": m.exp_level, "trophies": m.trophies,
                              "donations": m.donations, "donationsReceived": m.received, "clanRank": 0,
                              "league": m.league.name, "role": m.role.name})
        self.bot.logger.info("Done with SQL - Starting Google")
        conn.close()
        payload = {"type": "players", "data": to_google}
        url = "https://script.google.com/macros/s/AKfycbzhXbO1CCcRuPzTU0mos7MowcucvclAKokkTiq91463xW1ftQEO/exec"
        r = requests.post(url, data=json.dumps(payload))
        self.bot.logger.info("Oak data push complete.")

    @oak_data_push.before_loop
    async def before_oak_data_push(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=12.0)
    async def check_quercus(self):
        clan = await self.bot.coc.get_clan(clans['Reddit Quercus'])
        if not self.guild:
            self.guild = self.bot.get_guild(settings['discord']['oakguild_id'])
        quercus_role = self.guild.get_role(settings['oak_roles']['quercus'])
        not_in_links = []
        for member in clan.members:
            try:
                discord_id = await self.bot.links.get_discord_link(member.tag)
                if not discord_id:
                    not_in_links.append(f"{member.name} ({member.tag})")
                    continue
                discord_member = self.guild.get_member(discord_id)
                if not discord_member:
                    print(discord_id, type(discord_id))
                    continue
                if quercus_role not in discord_member.roles:
                    await discord_member.add_roles(quercus_role, "Auto-add in background. You're welcome!")
            except ValueError:
                not_in_links.append(f"{member.name} ({member.tag})")
        # if not_in_links:
        #     channel = self.guild.get_channel(settings['oak_channels']['test_chat'])
        #     new_line = "\n"
        #     await channel.send(f"The following players in Quercus are not in the links API:\n"
        #                        f"{new_line.join(not_in_links)}")

    @check_quercus.before_loop
    async def before_check_quercus(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=1.0)
    async def check_oak(self):
        clan = await self.bot.coc.get_clan(clans['Reddit Oak'])
        if not self.guild:
            self.guild = self.bot.get_guild(settings['discord']['oakguild_id'])
        quercus_role = self.guild.get_role(settings['oak_roles']['quercus'])
        not_in_links = []
        for member in clan.members:
            try:
                discord_id = self.bot.links.get_discord_link(member.tag)
                if not discord_id:
                    gc = gspread.oauth()
                    ot = gc.open("Oak Table")
                    sh = ot.worksheet("Current Members")
                    name_cell = sh.find(member.name)
                    if name_cell.row > 55:
                        self.bot.logger.debug(f"Skipping {member.name} ({member.tag}) since it appears they are new.")
                        not_in_links.append(f"{member.name} ({member.tag})")
                        continue
                    discord_id = sh.cell(name_cell.row, 9).value
                    if not discord_id:
                        # ID missing from Oak Table
                        continue
                discord_member = self.guild.get_member(discord_id)
                if quercus_role in discord_member.roles:
                    await discord_member.remove_roles(quercus_role, "Auto-remove in background because player is back "
                                                                    "in Oak. You're welcome!")
            except ValueError:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                line_num = exc_tb.tb_lineno
                self.bot.logger.info(f"check_oak: {line_num}: Value error dealing with {member.name} ({member.tag})")
        if not_in_links:
            channel = self.guild.get_channel(settings['oak_channels']['member_status_chat'])
            new_line = "\n"
            await channel.send(f"The following players in Oak are not in the links API:\n"
                               f"{new_line.join(not_in_links)}")

    @check_oak.before_loop
    async def before_check_oak(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Background(bot))
