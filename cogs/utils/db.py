import asyncpg
import pymssql
import requests

from config import settings


def get_link_token():
    """Retrieve new token for links API"""
    payload = {"username": settings['links']['user'], "password": settings['links']['pass']}
    url = "https://api.amazingspinach.com/login"
    r = requests.post(url, json=payload)
    return r.json()['token']


class Sql:
    def __init__(self, as_dict=False):
        self.as_dict = as_dict

    def __enter__(self):
        self.conn = pymssql.connect(settings['database']['server'],
                                    settings['database']['username'],
                                    settings['database']['password'],
                                    settings['database']['database'],
                                    autocommit=True)
        self.cursor = self.conn.cursor(as_dict=self.as_dict)
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()


class Psql:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def create_pool():
        pool = await asyncpg.create_pool(f"{settings['pg']['uri']}/rcsdata", max_size=85)
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

