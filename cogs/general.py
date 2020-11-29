import discord

from discord.ext import commands
from cogs.utils.db import Sql
from cogs.utils.constants import leagues_to_emoji
from cogs.utils.converters import PlayerConverter
from coc import enums
from config import settings, emojis, color_pick


class General(commands.Cog):
    """Default Arborist commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Auto-responder"""
        if message.author.name in ["The Arborist", "Oak WarBot", "Test Bot"]:
            return
        if "funnel" in message.content:
            return await message.channel.send("Learn how to funnel here - https://youtu.be/0rWN9FLMGT4 - "
                                              "or your leader will be very mad!")
        if "rules" in message.content:
            return await message.channel.send("Reddit Oak rules can be found here - "
                                              "https://www.reddit.com/r/CoC_RedditOak/wiki/moderation/general_rules")
        if any(word in message.content for word in ["signup", "sign-up", "sign up"]):
            return await message.channel.send(f"Please use `/war c#` or `/war call #` to call targets in "
                                              f"<#{str(settings['oak_channels']['coc_chat'])}> or "
                                              f"<#{str(settings['oak_channels']['oak_war'])}>")
        if "!th8" in message.content:
            await message.channel.send("https://photos.google.com/share/AF1QipPWoqacyT79PJJ4gL9P2hfHqWt_OkEFr-"
                                       "fjJSbFIgGhnF2aNM6MXMZtCzKKNo7JXw?key=N3JDOGRZd3oyMjc3dC1XZEhOVkl6cUNsb1lOSkFn")
        if "!th9" in message.content:
            await message.channel.send("https://photos.google.com/share/AF1QipN_cAARBgIIh_ZS01X2TbbkPrysVP9Kq3"
                                       "MtEeP9vUg1Y_CsocI5IiI2vfAaJt05Pg?key=WEJINW9XbVRjOHNkbDlSWEFJR3FJcVBWeUJSRVhR")
        if "!th10" in message.content:
            await message.channel.send("https://photos.google.com/share/AF1QipMuOnHRFk72JODAd0qrNUZs3aJliE1zWC17bgD"
                                       "u6olHzLmEQuGGCjzqRhz3NMDMNQ?key=NnNIVEpET2FscEJzVmpVVlcxRE1GdzhoSmRCeVFR")
        if "!th11" in message.content:
            await message.channel.send("https://photos.google.com/share/AF1QipPPrKuIqhzM82rebvhDEFxF-1dQeT7d48uWkn"
                                       "KY0wOvvK7DPpI98K-4ysCuyvEfOQ?key=S0JFSGdEemppVzRvN3BhV243TXhaODNlcWRXOE9R")

    @commands.command(name="player")
    async def player(self, ctx, *, player: PlayerConverter = None):
        """Provide details on the specified player"""
        if not player:
            self.bot.logger.warning(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                    f"Problem: No valid player name or tag was provided.")
            return await ctx.send(f"{emojis['other']['redx']} You must provide a valid in-game name or tag for this "
                                  f"command. Try `/player TubaKid`")
        # pull non-in-game stats from db
        with Sql() as cursor:
            sql = (f"SELECT tag, numWars, avgStars, warStats, joinDate, slackId "
                   f"FROM coc_oak_players "
                   f"WHERE tag = ?")
            cursor.execute(sql, player.tag[1:])
            oak_stats = cursor.fetchone()
        try:
            if not oak_stats:
                self.bot.logger.warning(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                        f"Problem: {player.name} not found in SQL database")
                return await ctx.send(f"{emojis['other']['redx']} The player you provided was not found in the "
                                      f"database. Please try again.")
        except:
            self.bot.logger.error(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                  f"Unknown error has occurred")
            return await ctx.send(f"{emojis['other']['redx']} Something has gone horribly wrong. "
                                  f"<@251150854571163648> I was trying to look up {player.name} "
                                  f"but the world conspired against me.")
        # retrieve player info from coc.py
        player_tag = f"#{oak_stats.tag}"
        player = await self.bot.coc.get_player(player_tag)
        troop_levels = builder_levels = spell_levels = hero_levels = builder_hero = sm_levels = ""
        sm_troops = enums.SIEGE_MACHINE_ORDER
        super_troops = enums.SUPER_TROOP_ORDER
        super_troops.append("Super Minion")
        count = 0
        for troop in player.home_troops:
            if troop.name in super_troops:
                # We're ignoring super troops at this time
                continue
            if troop.name not in sm_troops:
                count += 1
                if troop.name == "Minion":
                    count = 1
                    if troop_levels[-2:] == "\n":
                        troop_levels += "\n"
                    else:
                        troop_levels += "\n\n"
                troop_levels += f"{emojis['troops'][troop.name]}{str(troop.level)} "
                if count % 6 == 0:
                    troop_levels += "\n"
            else:
                sm_levels += f"{emojis['siege'][troop.name]}{str(troop.level)} "
        count = 0
        for spell in player.spells:
            count += 1
            if spell.name == "Poison Spell" and spell_levels[-2:] != "\n":
                spell_levels += "\n"
                count = 1
            spell_levels += f"{emojis['spells'][spell.name]}{str(spell.level)} "
            if count % 6 == 0:
                spell_levels += "\n"
        count = 0
        for troop in player.builder_troops:
            count += 1
            builder_levels += f"{emojis['build_troops'][troop.name]}{str(troop.level)} "
            if count % 6 == 0:
                builder_levels += "\n"
        # Test for number of heroes
        if len(player.heroes) > 0:
            for hero in player.heroes:
                if hero.name != "Battle Machine":
                    hero_levels += f"{emojis['heroes'][hero.name]}{str(hero.level)} "
                else:
                    builder_hero = f"{emojis['heroes'][hero.name]}{str(hero.level)}"
        embed = discord.Embed(title=f"{emojis['league'][leagues_to_emoji[player.league.name]]} "
                                    f"{player.name} "
                                    f"({player.tag})",
                              color=color_pick(226, 226, 26))
        embed.add_field(name="Town Hall",
                        value=f"{emojis['th_icon'][player.town_hall]} {str(player.town_hall)}",
                        inline=True)
        embed.add_field(name="Trophies", value=player.trophies, inline=True)
        embed.add_field(name="Best Trophies", value=player.best_trophies, inline=True)
        embed.add_field(name="War Stars", value=player.war_stars, inline=True)
        embed.add_field(name="Attack Wins", value=player.attack_wins, inline=True)
        embed.add_field(name="Defense Wins", value=player.defense_wins, inline=True)
        embed.add_field(name="Wars in Oak", value=oak_stats.numWars, inline=True)
        embed.add_field(name="Avg. Stars per War", value=str(round(oak_stats.avgStars, 2)), inline=True)
        embed.add_field(name="This Season", value=oak_stats.warStats, inline=False)
        embed.add_field(name="Troop Levels", value=troop_levels, inline=False)
        if sm_levels != "":
            embed.add_field(name="Siege Machines", value=sm_levels, inline=False)
        embed.add_field(name="Spell Levels", value=spell_levels, inline=False)
        if hero_levels != "":
            embed.add_field(name="Heroes", value=hero_levels, inline=False)
        embed.add_field(name="Builder Hall Level",
                        value=f"{emojis['bh_icon'][player.builder_hall]} {str(player.builder_hall)}",
                        inline=False)
        embed.add_field(name="Versus Trophies", value=str(player.versus_trophies), inline=True)
        embed.add_field(name="Versus Battle Wins", value=str(player.versus_attack_wins), inline=True)
        embed.add_field(name="Best Versus Trophies", value=str(player.best_versus_trophies), inline=True)
        embed.add_field(name="Troop Levels", value=builder_levels, inline=False)
        if builder_hero != "":
            embed.add_field(name="Hero", value=builder_hero, inline=False)
        embed.set_footer(icon_url=player.clan.badge.url,
                         text=f"Member of Reddit Oak since {oak_stats.joinDate.strftime('%e %B, %Y')}")
        self.bot.logger.debug(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                              f"Request complete: /player {player.name}")
        await ctx.send(embed=embed)

    @commands.command(name="avatar", hidden=True)
    async def avatar(self, ctx, user: discord.Member):
        # convert discord mention to user id only
        guild = ctx.bot.get_guild(settings['discord']['oakguild_id'])
        embed = discord.Embed(color=discord.Color.blue())
        embed.add_field(name=f"{user.name}#{user.discriminator}", value=user.display_name)
        embed.set_image(url=user.avatar_url_as(size=128))
        await ctx.send(embed=embed)
        self.bot.logger.debug(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                              f"Request complete: /avatar {user.display_name}")

    @avatar.error
    async def avatar_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("You may think so, but that's not a valid Discord user. Care to try again?")

    @commands.command(name="help", hidden=True)
    async def help(self, ctx, command: str = "all"):
        """ Welcome to The Arborist"""
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
                     "\n**slammer**: Stone Slammer"
                     "\n**barracks**: Siege Barracks")
            embed.add_field(name="/siege <siege type>", value=siege, inline=False)
        if command in ["all", "player"]:
            player = ("Display vital statistics on the requested player. This includes information "
                      "on in game stats as well as stats while in Reddit Oak.")
            embed.add_field(name="/player <in game name>", value=player, inline=False)
        if command in ["all", "avatar"]:
            avatar = "Provides an enlarged version of the specified player's avatar."
            embed.add_field(name="/avatar <Discord Mention or ID>", value=avatar, inline=False)
        if command == "elder":
            elder = "To display help for elder commands, please type /elder."
            embed.add_field(name="/elder", value=elder, inline=False)
        embed.set_footer(icon_url="https://openclipart.org/image/300px/svg_to_png/122449/1298569779.png",
                         text="The Arborist proudly maintained by TubaKid.")
        self.bot.logger.debug(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                              f"Request complete: /help {command}")
        await ctx.send(embed=embed)

    @commands.command(name="sheet")
    async def sheet(self, ctx):
        await ctx.send(settings['google']['oak_sheet'])

    @commands.command(name="siege", aliases=["sm"])
    async def siege_request(self, ctx, *, siege_req: str = "help"):
        """- For requesting siege machines

        Options:
         - ww, wall wrecker
         - air1, blimp, battle blimp, bb
         - air2, stone, slam, slammer, stone slammer
         - barracks, sb

         **Example:**
         /siege wall wrecker
         /siege blimp
         /siege Stone Slammer
         /siege barracks
         """
        user_id = ctx.author.id
        if siege_req == "help":
            embed = discord.Embed(title="The Arborist by Reddit Oak", color=color_pick(15, 250, 15))
            embed.add_field(name="Commands:", value="-----------", inline=True)
            siege = ("Posts request for the specified siege machine in Discord and tags those players that can donate."
                     "\n**ground**: Wall Wrecker"
                     "\n**blimp**: Battle Blimp"
                     "\n**slammer**: Stone Slammer"
                     "\n**barracks**: Siege Barracks")
            embed.add_field(name="/siege <siege type>", value=siege, inline=False)
            embed.set_footer(icon_url="https://openclipart.org/image/300px/svg_to_png/122449/1298569779.png",
                             text="The Arborist proudly maintained by TubaKid.")
            await ctx.send(embed=embed)
            return
        if siege_req in ["ww", "wall wrecker"]:
            siege_name = "Wall Wrecker"
            thumb = "https://coc.guide/static/imgs/troop/siege-machine-ram.png"
        elif siege_req in ["blimp", "air1", "bb", "battle blimp"]:
            siege_name = "Battle Blimp"
            thumb = "https://coc.guide/static/imgs/troop/siege-machine-flyer.png"
        elif siege_req in ["stone", "slammer", "slam", "air2", "stone slammer"]:
            siege_name = "Stone Slammer"
            thumb = "https://coc.guide/static/imgs/troop/siege-bowler-balloon.png"
        elif siege_req in ["barracks", "sb", "seige barracks", "baracks"]:
            siege_name = "Siege Barracks"
            thumb = "https://coc.guide/static/imgs/troop/siege-machine-carrier.png"
        else:
            await ctx.send("You have provided an invalid siege machine type. "
                           "Please specify `ground`, `blimp`, `slammer`, or `barracks`")
            return
        sent_msg = await ctx.send(f"One moment while I check to see who has those.")
        donors = []
        requestor = None
        # get requestor player tag from Discord ID
        clan = await self.bot.coc.get_clan("#CVCJR89")
        requestor_tag = await self.bot.links.get_linked_players(user_id)
        # Remove any links for player tags that aren't currently in Oak
        if len(requestor_tag) > 1:
            clan_tags = [x.tag for x in clan.members]
            for tag in requestor_tag:
                if tag not in clan_tags:
                    requestor_tag.remove(tag)
        # If still more than one, prompt user for correct player
        if len(requestor_tag) > 1:
            prompt_text = "You have more than one player in Reddit Oak. Please select the correct player:"
            counter = 1
            for tag in requestor_tag:
                player = await self.bot.coc.get_player(tag)
                prompt_text += f"\n{counter}. {player.name} ({player.tag})"
            prompt = ctx.prompt(prompt_text, additional_options=len(requestor_tag))
            requestor_tag = requestor_tag[prompt - 1]
        # find oak players with the requested siege machine
        async for player in clan.get_detailed_members():
            if siege_name in [troop.name for troop in player.siege_machines]:
                discord_id = await self.bot.links.get_discord_links(player.tag)
                donors.append(f"{player.name}: <@{discord_id}>")
            if requestor_tag == player.tag:
                requestor = player.name
        if not requestor:
            requestor = ctx.author.name
        await sent_msg.delete()
        embed = discord.Embed(title=f"{siege_name} Request",
                              description=f"{requestor} has requested a {siege_name}",
                              color=0xb5000)
        embed.set_footer(icon_url=thumb, text="Remember to select your siege machine when you attack!")
        content = "**Potential donors include:**\n"
        content += "\n".join(donors)
        await ctx.send(embed=embed)
        await ctx.send(content)

    @commands.command(name="nickname")
    async def nickname(self, ctx):
        await ctx.send("https://www.techuntold.com/change-nickname-discord/")

    @commands.command(name="invite")
    async def invite(self, ctx):
        await ctx.send("https://discord.me/redditoak")


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
