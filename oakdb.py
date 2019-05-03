import asyncpg
from config import settings


class OakDB:
    def __init__(self, bot):
        self.bot = bot
        self.test_channel = self.bot.get_channel(settings['oakChannels']['testChat'])

    async def create_pool(self):
        pool = await asyncpg.create_pool(settings['pg']['uri'])
        return pool

    async def link_user(self, player_tag, discord_id):
        conn = self.bot.pool
        sql = f"SELECT discord_id FROM rcs_discord_links WHERE tag = '{player_tag}'"
        row = await conn.fetchrow(sql)
        if row:
            if row('discord_id') == discord_id:
                # player record is already in db
                await self.test_channel.send(f"{player_tag} is already in the database.")
                pass
            # row exists but has a different discord_id
            sql = (f"UPDATE rcs_discord_links"
                   f"SET discord_id = {discord_id}"
                   f"WHERE player_tag = '{player_tag}'")
            await conn.execute(sql)
            await self.test_channel.send(f"{discord_id} so I updated it!")
            return
        # no player record in db
        sql = (f"INSERT INTO rcs_discord_links"
               f"VALUES ({discord_id}, '{player_tag}'")
        await conn.execute(sql)
        await self.test_channel.send(f"{player_tag} added to the database")
        conn.close()
