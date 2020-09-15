import asyncpg
import pyodbc

from config import settings


class Sql:
    def __enter__(self):
        driver = "ODBC Driver 17 for SQL Server"
        self.conn = pyodbc.connect(f"DRIVER={driver};"
                                   f"SERVER={settings['database']['server']};"
                                   f"DATABASE={settings['database']['database']};"
                                   f"UID={settings['database']['username']};"
                                   f"PWD={settings['database']['password']}")
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()


class Psql:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def create_pool():
        pool = await asyncpg.create_pool(f"{settings['pg']['uri']}/tubadata", max_size=85)
        return pool

    async def link_user(self, player_tag, discord_id):
        conn = self.bot.pool
        sql = ("INSERT INTO rcs_discord_links (discord_id, player_tag) "
               "VALUES ($1, $2)"
               "ON CONFLICT (player_tag) DO "
               "UPDATE "
               "SET discord_id = $1 "
               "WHERE rcs_discord_links.player_tag = $2")
        await conn.execute(sql, discord_id, player_tag)

