import discord
import pymssql
from discord.ext import commands
from config import settings, emojis, color_pick, logger


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
        if any(word in message.content for word in ["signup", "sign-up", "sign up"]):
            await message.channel.send(f"Please use `/war c#` or `/war call #` to call targets in "
                                       f"<#{str(settings['oakChannels']['cocChat'])}> or "
                                       f"<#{str(settings['oakChannels']['oakWar'])}>")
            return

    @commands.command(name="player")
    async def player(self, ctx, *, player_name: str = "x"):
        """Provide details on the specified player"""
        if player_name == "x":
            logger(ctx, "WARNING", "general", message="Name not provided")
            await ctx.send(f"{emojis['other']['redx']} You must provide an in-game name for this "
                           f"command. Try /player TubaKid")
            return
        conn = pymssql.connect(settings['database']['server'],
                               settings['database']['username'],
                               settings['database']['password'],
                               settings['database']['database'])
        cursor = conn.cursor(as_dict=True)
        cursor.execute(f"SELECT * FROM coc_oak_playerStats WHERE playerName = '{player_name}'")
        try:
            row = cursor.fetchone()
            if row is None:
                logger(ctx, "WARNING", "general", message=f"{player_name} not found in SQL database.")
                await ctx.send(f"{emojis['other']['redx']} The player you provided was not found in the database. "
                               f"Please try again.")
                return
        except:
            logger(ctx, "ERROR", "general", {"Player": player_name}, "Unknown error occurred")
            await ctx.send(f"{emojis['other']['redx']} Something has gone horribly wrong. <@251150854571163648> "
                           f"I was trying to look up {player_name} but the world conspired against me.")
            return

        troopLevels = emojis['troops']['barb'] + str(row['barb'])
        troopLevels += "    " + emojis['troops']['arch'] + str(row['archer']) if row['archer'] > 0 else ""
        troopLevels += "    " + emojis['troops']['goblin'] + str(row['goblin']) if row['goblin'] > 0 else ""
        troopLevels += "    " + emojis['troops']['giant'] + str(row['giant']) if row['giant'] > 0 else ""
        troopLevels += "    " + emojis['troops']['wb'] + str(row['wallbreaker']) if row['wallbreaker'] > 0 else ""
        troopLevels += "\n" + emojis['troops']['loon'] + str(row['balloon']) if row['balloon'] > 0 else ""
        troopLevels += "    " + emojis['troops']['wiz'] + str(row['wizard']) if row['wizard'] > 0 else ""
        troopLevels += "    " + emojis['troops']['healer'] + str(row['healer']) if row['healer'] > 0 else ""
        troopLevels += "    " + emojis['troops']['drag'] + str(row['dragon']) if row['dragon'] > 0 else ""
        troopLevels += "\n" + emojis['troops']['pekka'] + str(row['pekka']) if row['pekka'] > 0 else ""
        troopLevels += "    " + emojis['troops']['babydrag'] + str(row['babyDrag']) if row['babyDrag'] > 0 else ""
        troopLevels += "    " + emojis['troops']['miner'] + str(row['miner']) if row['miner'] > 0 else ""
        troopLevels += "    " + emojis['troops']['edrag'] + str(row['edrag']) if row['edrag'] > 0 else ""
        troopLevels += "\n" + emojis['troops']['minion'] + str(row['minion']) if row['minion'] > 0 else ""
        troopLevels += "    " + emojis['troops']['hogs'] + str(row['hogRider']) if row['hogRider'] > 0 else ""
        troopLevels += "    " + emojis['troops']['valk'] + str(row['valkyrie']) if row['valkyrie'] > 0 else ""
        troopLevels += "    " + emojis['troops']['golem'] + str(row['golem']) if row['golem'] > 0 else ""
        troopLevels += "    " + emojis['troops']['witch'] + str(row['witch']) if row['witch'] > 0 else ""
        troopLevels += "\n" + emojis['troops']['lava'] + str(row['lavaHound']) if row['lavaHound'] > 0 else ""
        troopLevels += "    " + emojis['troops']['bowler'] + str(row['bowler']) if row['bowler'] > 0 else ""
        troopLevels += "    " + emojis['troops']['icegolem'] + str(row['icegolem']) if row['icegolem'] > 0 else ""
        spellLevels = emojis['spells']['light'] + str(row['light'])
        spellLevels += "    " + emojis['spells']['heal'] + str(row['heal']) if row['heal'] > 0 else ""
        spellLevels += "    " + emojis['spells']['rage'] + str(row['rage']) if row['rage'] > 0 else ""
        spellLevels += "    " + emojis['spells']['jump'] + str(row['jump']) if row['jump'] > 0 else ""
        spellLevels += "    " + emojis['spells']['freeze'] + str(row['freeze']) if row['freeze'] > 0 else ""
        spellLevels += "\n" + emojis['spells']['poison'] + str(row['poison']) if row['poison'] > 0 else ""
        spellLevels += "    " + emojis['spells']['eq'] + str(row['earthquake']) if row['earthquake'] > 0 else ""
        spellLevels += "    " + emojis['spells']['haste'] + str(row['haste']) if row['haste'] > 0 else ""
        spellLevels += "    " + emojis['spells']['clone'] + str(row['clone']) if row['clone'] > 0 else ""
        spellLevels += "    " + emojis['spells']['skell'] + str(row['skeleton']) if row['skeleton'] > 0 else ""
        spellLevels += "    " + emojis['spells']['bat'] + str(row['bat']) if row['bat'] > 0 else ""
        builderLevels = emojis['buildTroops']['rbarb'] + str(row['ragedBarb'])
        builderLevels += "    " + emojis['buildTroops']['sarch'] + str(row['sneakyArcher']) if row['sneakyArcher'] > 0 else ""
        builderLevels += "    " + emojis['buildTroops']['beta'] + str(row['betaMinion']) if row['betaMinion'] > 0 else ""
        builderLevels += "    " + emojis['buildTroops']['boxer'] + str(row['boxerGiant']) if row['boxerGiant'] > 0 else ""
        builderLevels += "    " + emojis['buildTroops']['bomber'] + str(row['bomber']) if row['bomber'] > 0 else ""
        builderLevels += "\n" + emojis['buildTroops']['pekka'] + str(row['superPekka']) if row['superPekka'] > 0 else ""
        builderLevels += "    " + emojis['buildTroops']['cannon'] + str(row['cannonCart']) if row['cannonCart'] > 0 else ""
        builderLevels += "    " + emojis['buildTroops']['dropship'] + str(row['dropShip']) if row['dropShip'] > 0 else ""
        builderLevels += "    " + emojis['buildTroops']['babydrag'] + str(row['vsBabyDragon']) if row['vsBabyDragon'] > 0 else ""
        builderLevels += "    " + emojis['buildTroops']['witch'] + str(row['nightWitch']) if row['nightWitch'] > 0 else ""
        if row['barbKing'] > 0:
            heroTitle = 'Hero Levels'
            heroLevels = emojis['heroes']['bk'] + str(row['barbKing'])
            heroLevels += "    " + emojis['heroes']['aq'] + str(row['archQueen']) if row['archQueen'] > 0 else ""
            heroLevels += "    " + emojis['heroes']['gw'] + str(row['grandWarden']) if row['grandWarden'] > 0 else ""
        else:
            heroTitle = heroLevels = ""
        builderHero = emojis['heroes']['bm'] + str(row['battleMachine'])
        embed = discord.Embed(title=f"{emojis['league'][row['leagueEmoji'][1:-1]]} {row['playerName'].strip()} "
                                    f"({row['tag'].strip()})",
                              color=color_pick(226, 226, 26))
        embed.add_field(name="Town Hall",
                        value=f"{emojis['thIcon'][row['thLevel']]} {str(row['thLevel'])}",
                        inline=True)
        embed.add_field(name="Trophies", value=row['trophies'], inline=True)
        embed.add_field(name="Best Trophies", value=row['bestTrophies'], inline=True)
        embed.add_field(name="War Stars", value=row['warStars'], inline=True)
        embed.add_field(name="Attack Wins", value=row['attackWins'], inline=True)
        embed.add_field(name="Defense Wins", value=row['defenseWins'], inline=True)
        embed.add_field(name="Wars in Oak", value=row['numWars'], inline=True)
        embed.add_field(name="Avg. Stars per War", value=str(round(row['avgStars'], 2)), inline=True)
        embed.add_field(name="This Season", value=row['warStats'], inline=False)
        embed.add_field(name="Troop Levels", value=troopLevels, inline=False)
        embed.add_field(name="Spell Levels", value=spellLevels, inline=False)
        embed.add_field(name=heroTitle, value=heroLevels, inline=False)
        embed.add_field(name="Builder Hall Level",
                        value=f"{emojis['bhIcon'][row['builderHall']]} {str(row['builderHall'])}",
                        inline=False)
        embed.add_field(name="Versus Trophies", value=str(row['vsTrophies']), inline=True)
        embed.add_field(name="Versus Battle Wins", value=str(row['versusBattleWins']), inline=True)
        embed.add_field(name="Best Versus Trophies", value=str(row['bestVsTrophies']), inline=True)
        embed.add_field(name="Troop Levels", value=builderLevels, inline=False)
        embed.add_field(name="Hero Levels", value=builderHero, inline=False)
        embed.set_footer(icon_url="http://www.mayodev.com/images/coc/oakbadge.png",
                         text=f"Member of Reddit Oak since {row['joinDate'].strftime('%e %B, %Y')}")
        logger(ctx, "INFO", "general", {"Player": player_name})
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
        logger(ctx, "INFO", "general", {"Member": member})

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
            logger(ctx, "WARN", "general", {"Command": command})
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
        logger(ctx, "INFO", "general", {"Command": command})
        await ctx.send(embed=embed)

    @commands.command(name="siege", aliases=["sm"])
    async def siege_request(self, ctx, *, siege_type: str = "help"):
        """- For requesting siege machines
        Options:
         - ground, ww, wall wrecker
         - air1, blimp, battle blimp, bb
         - air2, stone, slam, slammer, stone slammer"""
        userId = ctx.author.id
        if siege_type == "help":
            embed = discord.Embed(title="The Arborist by Reddit Oak", color=color_pick(15, 250, 15))
            embed.add_field(name="Commands:", value="-----------", inline=True)
            siege = ("Posts request for the specified siege machine in Discord and tags those players that can donate."
                     "\n**ground**: Wall Wrecker"
                     "\n**blimp**: Battle Blimp"
                     "\n**slammer**: Stone Slammer")
            embed.add_field(name="/siege <siege type>", value=siege, inline=False)
            embed.set_footer(icon_url="https://openclipart.org/image/300px/svg_to_png/122449/1298569779.png",
                             text="The Arborist proudly maintained by TubaKid.")
            logger(ctx, "INFO", "general", {"Command": "siege", "Argument": "help"})
            await ctx.send(embed=embed)
            return
        if siege_type in ["ground", "ww", "wall wrecker"]:
            siegeType = "wallWrecker"
            siegeName = "Wall Wrecker"
            thumb = "https://coc.guide/static/imgs/troop/siege-machine-ram.png"
        elif siege_type in ["blimp", "air1", "bb", "battle blimp"]:
            siegeType = "battleBlimp"
            siegeName = "Battle Blimp"
            thumb = "https://coc.guide/static/imgs/troop/siege-machine-flyer.png"
        elif siege_type in ["stone", "slammer", "slam", "air2", "stone slammer"]:
            siegeType = "stoneSlammer"
            siegeName = "Stone Slammer"
            thumb = "https://coc.guide/static/imgs/troop/siege-bowler-balloon.png"
        else:
            await ctx.send("You have provided an invalid siege machine type. "
                           "Please specify `ground`, `blimp`, or `slammer`")
            return
        conn = pymssql.connect(settings['database']['server'],
                               settings['database']['username'],
                               settings['database']['password'],
                               settings['database']['database'])
        cursor = conn.cursor(as_dict=True)
        cursor.execute("SELECT playerName FROM coc_oak_players WHERE slackId = '{}'".format(userId))
        row = cursor.fetchone()
        requestor = row['playerName']
        cursor.execute("SELECT playerName, slackId FROM coc_oak_playerStats WHERE {} >    0".format(siegeType))
        fetched = cursor.fetchall()
        conn.close()
        donors = []
        for row in fetched:
            donors.append(f"{row['playerName'].rstrip()}: <@{row['slackId']}>")
        embed = discord.Embed(title=f"{siegeName} Request",
                              description=f"{requestor} has requested a {siegeName}",
                              color=0xb5000)
        # embed.add_field(name = "Potential donors include:", value = "\n".join(donors))
        embed.set_footer(icon_url=thumb, text="Remember to select your seige machine when you attack!")
        content = "**Potential donors include:**\n"
        content += "\n".join(donors)
        logger(ctx, "INFO", "general", {"Command": "siege", "Argument": siegeType})
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


def setup(bot):
    bot.add_cog(General(bot))
