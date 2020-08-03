import asyncpg
# import pymssql
import pyodbc
import requests

from config import settings


def get_link_token():
    """Retrieve new token for links API"""
    payload = {"username": settings['links']['user'], "password": settings['links']['pass']}
    url = "https://api.amazingspinach.com/login"
    r = requests.post(url, json=payload)
    return r.json()['token']


def get_discord_id(tag):
    """Get discord ID from player tag
    Returns single Discord ID because a player tag will only ever have one Discord ID"""
    token = get_link_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    base_url = "https://api.amazingspinach.com/links/%23"
    if tag.startswith("#"):
        tag = tag[1:]
    url = base_url + tag
    r = requests.get(url, headers=headers)
    data = r.json()
    if data:
        return int(data[0]['discordId'])
    else:
        return None


def get_player_tag(discord_id):
    """Get player tag from Discord ID
    Returns multiple player tags if linked to more than one player"""
    token = get_link_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    base_url = "https://api.amazingspinach.com/links/"
    url = f"{base_url}{discord_id}"
    r = requests.get(url, headers=headers)
    data = r.json()
    tags = [x['playerTag'] for x in data]
    return tags


def get_discord_batch(tag_list):
    """Get discord IDs for a list of player tags"""
    token = get_link_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = "https://api.amazingspinach.com/links/batch"
    r = requests.post(url, headers=headers, json=tag_list)
    data = r.json()
    response = {}
    for row in data:
        response[row['playerTags'][0]] = row['discordId']
    return response


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

