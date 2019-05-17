import discord
import pymssql
import asyncpg
from discord.ext import commands
from config import settings, emojis, color_pick


class General(commands.Cog):
    """Default Arborist commands"""
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        """Auto-responder"""
        if message.author.name == "The Arborist" or message.author.name == "Oak WarBot":
            return
        if "funnel" in message.content:
            await message.channel.send("Learn how to funnel here - https://youtu.be/0rWN9FLMGT4 - "
                                       "or your leader will be very mad!")
            return
        if "rules" in message.content:
            await message.channel.send("Reddit Oak rules can be found here - "
                                       "https://www.reddit.com/r/CoC_RedditOak/wiki/moderation/general_rules")
            return
        if "!invite" in message.content:
            await message.channel.send("https://discord.me/redditoak")
            return
        if any(word in message.content for word in ["signup", "sign-up", "sign up"]):
            await message.channel.send(f"Please use `/war c#` or `/war call #` to call targets in "
                                       f"<#{str(settings['oakChannels']['cocChat'])}> or "
                                       f"<#{str(settings['oakChannels']['oakWar'])}>")
            return

    @commands.command(name="player")
    async def player(self, ctx, *, player_name: str = "x"):
        """Provide details on the specified player"""
        if player_name == "x":
            self.bot.logger.warning(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                    f"Problem: No player name was provided.")
            await ctx.send(f"{emojis['other']['redx']} You must provide an in-game name for this "
                           f"command. Try /player TubaKid")
            return
        # pull non-in-game stats from db
        conn = self.bot.db.pool
        sql = f"SELECT * FROM oak_members WHERE player_name = '{player_name}'"
        oak_stats = await conn.fetchrow(sql)
        try:
            if oak_stats is None:
                self.bot.logger.warning(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                        f"Problem: {player_name} not found in PostgreSQL database")
                await ctx.send(f"{emojis['other']['redx']} The player you provided was not found in the database. "
                               f"Please try again.")
                return
        except:
            self.bot.logger.error(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                  f"Unknown error has occurred")
            await ctx.send(f"{emojis['other']['redx']} Something has gone horribly wrong. <@251150854571163648> "
                           f"I was trying to look up {player_name} but the world conspired against me.")
            return
        # retrieve player info from coc.py
        player_tag = f"#{oak_stats['player_tag']}"
        player = await self.bot.coc_client.get_player(player_tag)
        troop_levels = builder_levels = spell_levels = hero_levels = builder_hero = sm_levels = ""
        sm_troops = ["Wall Wrecker", "Battle Blimp", "Stone Slammer"]
        count = 0
        for name, troop in player.ordered_home_troops.items():
            if name not in sm_troops:
                count += 1
                if name == "Minion":
                    count = 1
                    if troop_levels[-2:] == "\n":
                        troop_levels += "\n"
                    else:
                        troop_levels += "\n\n"
                troop_levels += f"{emojis['troops'][name]}{str(troop.level)} "
                if count % 6 == 0:
                    troop_levels += "\n"
            else:
                sm_levels += f"{emojis['siege'][name]}{str(troop.level)} "
        count = 0
        for name, spell in player.ordered_spells.items():
            count += 1
            if name == "Poison Spell" and spell_levels[-2:] != "\n":
                spell_levels += "\n"
                count = 1
            spell_levels += f"{emojis['spells'][name]}{str(spell.level)} "
            if count % 6 == 0:
                spell_levels += "\n"
        count = 0
        for name, troop in player.ordered_builder_troops.items():
            count += 1
            builder_levels += f"{emojis['buildTroops'][name]}{str(troop.level)} "
            if count % 6 == 0:
                builder_levels += "\n"
        # Test for number of heroes
        if len(player.ordered_heroes) > 0:
            for name, hero in player.ordered_heroes.items():
                if name != "Battle Machine":
                    hero_levels += f"{emojis['heroes'][name]}{str(hero.level)} "
                else:
                    builder_hero = f"{emojis['heroes'][name]}{str(hero.level)}"
        embed = discord.Embed(title=f"{emojis['league'][get_league_emoji(player.league.name)]} "
                                    f"{player.name} "
                                    f"({player.tag})",
                              color=color_pick(226, 226, 26))
        embed.add_field(name="Town Hall",
                        value=f"{emojis['thIcon'][player.town_hall]} {str(player.town_hall)}",
                        inline=True)
        embed.add_field(name="Trophies", value=player.trophies, inline=True)
        embed.add_field(name="Best Trophies", value=player.best_trophies, inline=True)
        embed.add_field(name="War Stars", value=player.war_stars, inline=True)
        embed.add_field(name="Attack Wins", value=player.attack_wins, inline=True)
        embed.add_field(name="Defense Wins", value=player.defense_wins, inline=True)
        embed.add_field(name="Wars in Oak", value=oak_stats['num_wars'], inline=True)
        embed.add_field(name="Avg. Stars per War", value=str(round(oak_stats['avg_stars'], 2)), inline=True)
        embed.add_field(name="This Season", value=oak_stats['season_wars'], inline=False)
        embed.add_field(name="Troop Levels", value=troop_levels, inline=False)
        if sm_levels != "":
            embed.add_field(name="Siege Machines", value=sm_levels, inline=False)
        embed.add_field(name="Spell Levels", value=spell_levels, inline=False)
        if hero_levels != "":
            embed.add_field(name="Heroes", value=hero_levels, inline=False)
        embed.add_field(name="Builder Hall Level",
                        value=f"{emojis['bhIcon'][player.builder_hall]} {str(player.builder_hall)}",
                        inline=False)
        embed.add_field(name="Versus Trophies", value=str(player.versus_trophies), inline=True)
        embed.add_field(name="Versus Battle Wins", value=str(player.versus_attacks_wins), inline=True)
        embed.add_field(name="Best Versus Trophies", value=str(player.best_versus_trophies), inline=True)
        embed.add_field(name="Troop Levels", value=builder_levels, inline=False)
        if builder_hero != "":
            embed.add_field(name="Hero", value=builder_hero, inline=False)
        embed.set_footer(icon_url="http://www.mayodev.com/images/coc/oakbadge.png",
                         text=f"Member of Reddit Oak since {oak_stats['join_date'].strftime('%e %B, %Y')}")
        self.bot.logger.debug(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                              f"Request complete: /player {player_name}")
        await ctx.send(embed=embed)

    @commands.command(name="avatar", hidden=True)
    async def avatar(self, ctx, member):
        # convert discord mention to user id only
        if member.startswith("<"):
            discord_id = "".join(member[2:-1])
            if discord_id.startswith("!"):
                discord_id = discord_id[1:]
        else:
            await ctx.send(emojis['other']['redx'] + " I don't believe that's a real Discord user. "
                                                     "Please make sure you are using the '@' prefix.")
            return
        guild = ctx.bot.get_guild(settings['discord']['oakGuildId'])
        is_user, user = is_discord_user(guild, int(discord_id))
        if not is_user:
            await ctx.send(f"{emojis['other']['redx']} User provided "
                           f"**{member}** is not a member of this discord server.")
            return
        embed = discord.Embed(color=discord.Color.blue())
        embed.add_field(name=f"{user.name}#{user.discriminator}", value=user.display_name)
        embed.set_image(url=user.avatar_url_as(size=128))
        await ctx.send(embed=embed)
        self.bot.logger.debug(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                              f"Request complete: /avatar {member}")

    @commands.command(name="help", hidden=True)
    async def help(self, ctx, command: str = "all"):
        """ Welcome to tThe Arborist"""
        desc = """All commands must begin with a slash.

        You can type /help <command> to display only the help for that command."""
        # ignore requests for help with the war command
        if command == "war":
            return
        # respond if help is requested for a command that does not exist
        if command not in ["all", "siege", "player", "elder"]:
            self.bot.logger.warning(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                    f"Problem: /help {command} - command does not exist")
            await ctx.send(f"{emojis['other']['redx']} You have provided a command that does not exist. "
                           f"Perhaps try /help to see all commands.")
            return
        embed = discord.Embed(title="The Arborist by Reddit Oak", description=desc, color=color_pick(15, 250, 15))
        embed.add_field(name="Commands:", value="-----------", inline=True)
        if command in ["all", "siege"]:
            siege = ("Posts request for the specified siege machine in Discord and tags those players that can donate."
                     "\n**ground**: Wall Wrecker"
                     "\n**blimp**: Battle Blimp"
                     "\n**slammer**: Stone Slammer")
            embed.add_field(name="/siege <siege type>", value=siege, inline=False)
        if command in ["all", "player"]:
            player = ("Display vital statistics on the requested player. This includes information "
                      "on in game stats as well as stats while in Reddit Oak.")
            embed.add_field(name="/player <in game name>", value=player, inline=False)
        if command == "elder":
            elder = "To display help for elder commands, please type /elder."
            embed.add_field(name="/elder", value=elder, inline=False)
        embed.set_footer(icon_url="https://openclipart.org/image/300px/svg_to_png/122449/1298569779.png",
                         text="The Arborist proudly maintained by TubaKid.")
        self.bot.logger.debug(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                              f"Request complete: /help {command}")
        await ctx.send(embed=embed)

    @commands.command(name="siege", aliases=["sm"])
    async def siege_request(self, ctx, *, siege_req: str = "help"):
        """- For requesting siege machines
        Options:
         - ground, ww, wall wrecker
         - air1, blimp, battle blimp, bb
         - air2, stone, slam, slammer, stone slammer"""
        user_id = ctx.author.id
        if siege_req == "help":
            embed = discord.Embed(title="The Arborist by Reddit Oak", color=color_pick(15, 250, 15))
            embed.add_field(name="Commands:", value="-----------", inline=True)
            siege = ("Posts request for the specified siege machine in Discord and tags those players that can donate."
                     "\n**ground**: Wall Wrecker"
                     "\n**blimp**: Battle Blimp"
                     "\n**slammer**: Stone Slammer")
            embed.add_field(name="/siege <siege type>", value=siege, inline=False)
            embed.set_footer(icon_url="https://openclipart.org/image/300px/svg_to_png/122449/1298569779.png",
                             text="The Arborist proudly maintained by TubaKid.")
            await ctx.send(embed=embed)
            return
        if siege_req in ["ground", "ww", "wall wrecker"]:
            siege_type = "wallWrecker"
            siege_name = "Wall Wrecker"
            thumb = "https://coc.guide/static/imgs/troop/siege-machine-ram.png"
        elif siege_req in ["blimp", "air1", "bb", "battle blimp"]:
            siege_type = "battleBlimp"
            siege_name = "Battle Blimp"
            thumb = "https://coc.guide/static/imgs/troop/siege-machine-flyer.png"
        elif siege_req in ["stone", "slammer", "slam", "air2", "stone slammer"]:
            siege_type = "stoneSlammer"
            siege_name = "Stone Slammer"
            thumb = "https://coc.guide/static/imgs/troop/siege-bowler-balloon.png"
        else:
            await ctx.send("You have provided an invalid siege machine type. "
                           "Please specify `ground`, `blimp`, or `slammer`")
            return
        conn = self.bot.db.pool
        sql = "SELECT player_tag, discord_id FROM oak_discord"
        rows = await conn.fetch(sql)
        discord_dict = {}
        for row in rows:
            discord_dict[row['player_tag']] = row['discord_id']
        clan = await self.bot.coc_client.get_clan("#CVCJR89")
        donors = []
        async for player in clan.get_detailed_members():
            troops = player.home_troops_dict("name")
            if siege_name in troops.keys():
                donors.append(f"{player.name}: {discord_dict[player.tag[1:]]}")
        # conn = pymssql.connect(settings['database']['server'],
        #                        settings['database']['username'],
        #                        settings['database']['password'],
        #                        settings['database']['database'])
        # cursor = conn.cursor(as_dict=True)
        # cursor.execute(f"SELECT playerName FROM coc_oak_players WHERE slackId = '{user_id}'")
        # row = cursor.fetchone()
        requestor = row['playerName']
        # cursor.execute(f"SELECT playerName, slackId FROM coc_oak_playerStats WHERE {siege_type} >    0")
        # fetched = cursor.fetchall()
        # conn.close()
        # donors = []
        # for row in fetched:
        #     donors.append(f"{row['playerName'].rstrip()}: <@{row['slackId']}>")
        embed = discord.Embed(title=f"{siege_name} Request",
                              description=f"{requestor} has requested a {siege_name}",
                              color=0xb5000)
        # embed.add_field(name = "Potential donors include:", value = "\n".join(donors))
        embed.set_footer(icon_url=thumb, text="Remember to select your seige machine when you attack!")
        content = "**Potential donors include:**\n"
        content += "\n".join(donors)
        await ctx.send(embed=embed)
        await ctx.send(content)


def is_discord_user(guild, discord_id):
    try:
        user = guild.get_member(discord_id)
        if user is None:
            return False, None
        else:
            return True, user
    except:
        return False, None


def get_league_emoji(league_name):
    leagues = [
        ("Titan League I", "titan1"),
        ("Titan League II", "titan2"),
        ("Titan League III", "titan3"),
        ("Champion League I", "champs1"),
        ("Champion League II", "champs2"),
        ("Champion League III", "champs3"),
        ("Master League I", "masters1"),
        ("Master League II", "masters2"),
        ("Master League III", "masters3"),
        ("Crystal League I", "crystal1"),
        ("Crystal League II", "crystal2"),
        ("Crystal League III", "crystal3"),
        ("Gold League I", "gold1"),
        ("Gold League II", "gold2"),
        ("Gold League III", "gold3"),
        ("Silver League I", "silver1"),
        ("Silver League II", "silver2"),
        ("Silver League III", "silver3"),
        ("Bronze League I", "bronze1"),
        ("Bronze League II", "bronze2"),
        ("Bronze League III", "bronze3"),
        ("Unranked", "unranked")
    ]
    for league in leagues:
        if league_name in league:
            return league[1]



def setup(bot):
    bot.add_cog(General(bot))
