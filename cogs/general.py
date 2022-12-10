import coc
import nextcord
import gspread

from nextcord import ui, Interaction, SlashOption
from nextcord.ext import commands
from cogs.utils.constants import leagues_to_emoji
from cogs.utils.converters import PlayerConverter
from coc import enums
from config import settings, emojis, color_pick


# Connect to Google Sheets using gspread
gc = gspread.service_account(filename="service_account.json")
spreadsheet = gc.open_by_key(settings['google']['oak_table_id'])
curr_member_range = "A3:D52"
new_member_range = "A57:D61"


class Button(ui.Button):
    def __init__(self, player):
        super().__init__(
            label=player.name,
            style=nextcord.ButtonStyle.blurple,
            custom_id=player.tag,
            emoji=emojis['th_icon'][player.town_hall]
        )

    async def callback(self, interaction: Interaction):
        self.view.value = self.custom_id
        self.view.stop()


class ButtonView(nextcord.ui.View):
    def __init__(self, players):
        super().__init__()
        self.value = None

        for player in players:
            self.add_item(Button(player))


class General(commands.Cog):
    """Default Arborist commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Auto-responder"""
        if message.author.name in ["The Arborist", "Test Bot"]:
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
        # Get join date from Oak Table
        sheet = spreadsheet.worksheet("Current Members")
        cell = sheet.find(player.tag)
        if cell:
            join_date = sheet.cell(cell.row, 4).value
        else:
            join_date = "unknown"
        # retrieve player info from coc.py
        player = await self.bot.coc.get_player(player.tag)
        troop_levels = builder_levels = spell_levels = hero_levels = hero_pets_levels = builder_hero = \
            sm_levels = super_troop_levels = ""
        sm_troops = enums.SIEGE_MACHINE_ORDER
        super_troops = enums.SUPER_TROOP_ORDER
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
                if troop.name not in enums.HERO_PETS_ORDER:
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
        count = 0
        # Handle Super Troops
        for troop in player.home_troops:
            if troop.name in super_troops:
                count += 1
                if troop.is_active:
                    super_troop_levels += f"{emojis['super_troops_active'][troop.name]}{str(troop.level)} "
                else:
                    super_troop_levels += f"{emojis['super_troops'][troop.name]}{str(troop.level)} "
                if count % 6 == 0:
                    super_troop_levels += "\n"
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
            for troop in player.home_troops:
                if troop.name in enums.HERO_PETS_ORDER:
                    hero_pets_levels += f"{emojis['hero_pets'][troop.name]}{str(troop.level)} "
        embed = nextcord.Embed(title=f"{emojis['league'][leagues_to_emoji[player.league.name]]} "
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
        war_preference = "Opted In" if player.war_opted_in else "Opted Out"
        embed.add_field(name="War Preference", value=war_preference, inline=False)
        embed.add_field(name="Troop Levels", value=troop_levels, inline=False)
        if super_troop_levels != "":
            embed.add_field(name="Super Troops", value=super_troop_levels, inline=False)
        if sm_levels != "":
            embed.add_field(name="Siege Machines", value=sm_levels, inline=False)
        embed.add_field(name="Spell Levels", value=spell_levels, inline=False)
        if hero_levels != "":
            embed.add_field(name="Heroes", value=hero_levels, inline=False)
        if hero_pets_levels != "":
            embed.add_field(name="Hero Pets", value=hero_pets_levels, inline=False)
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
                         text=f"Member of Reddit Oak since {join_date}")
        self.bot.logger.debug(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                              f"Request complete: /player {player.name}")
        await ctx.send(embed=embed)

    @nextcord.slash_command(name="avatar", guild_ids=[settings['discord']['oakguild_id']])
    async def avatar(self, interaction: Interaction, user: nextcord.Member):
        """Responds with an enlarged version of the user's avatar."""
        embed = nextcord.Embed(color=nextcord.Color.blue())
        embed.add_field(name=f"{user.name}#{user.discriminator}", value=user.display_name)
        embed.set_image(url=user.avatar.url)
        await interaction.response.send_message(embed=embed)
        self.bot.logger.debug(f"{interaction.application_command} by {interaction.user.display_name} in "
                              f"{interaction.channel}")

    @commands.command(name="help", hidden=True)
    async def help(self, ctx, command: str = "all"):
        """ Welcome to The Arborist"""
        desc = """All commands must begin with a period.

        You can type .help <command> to display only the help for that command."""
        # ignore requests for help with the war command
        if command == "war":
            return
        # respond if help is requested for a command that does not exist
        if command not in ["all", "siege", "player", "elder"]:
            self.bot.logger.warning(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                    f"Problem: .help {command} - command does not exist")
            await ctx.send(f"{emojis['other']['redx']} You have provided a command that does not exist. "
                           f"Perhaps try .help to see all commands.")
            return
        embed = nextcord.Embed(title="The Arborist by Reddit Oak", description=desc, color=color_pick(15, 250, 15))
        embed.add_field(name="Commands:", value="-----------", inline=True)
        if command in ["all", "player"]:
            player = ("Display vital statistics on the requested player. This includes information "
                      "on in game stats as well as stats while in Reddit Oak.")
            embed.add_field(name=".player <in game name>", value=player, inline=False)
        embed.set_footer(icon_url="https://openclipart.org/image/300px/svg_to_png/122449/1298569779.png",
                         text="The Arborist proudly maintained by TubaKid.")
        self.bot.logger.debug(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                              f"Request complete: .help {command}")
        await ctx.send(embed=embed)

    @nextcord.slash_command(name="sm", guild_ids=[settings['discord']['oakguild_id']])
    async def siege(self, interaction: Interaction, *, siege_req):
        """For requesting siege machine donations

        Options:
         - ww, wall wrecker
         - air1, blimp, battle blimp, bb
         - air2, stone, slam, slammer, stone slammer
         - barracks, sb
         - log, launcher, log launcher
         - flame, flinger, flame flinger

         **Example:**
         /siege wall wrecker
         /siege blimp
         /siege Stone Slammer
         /siege barracks
         /siege ff
         """
        user_id = interaction.user.id
        channel = interaction.channel
        if siege_req == "help":
            embed = nextcord.Embed(title="The Arborist by Reddit Oak", color=color_pick(15, 250, 15))
            embed.add_field(name="Commands:", value="-----------", inline=True)
            siege = ("Posts request for the specified siege machine in Discord and tags those players that can donate."
                     "\n**ground**: Wall Wrecker"
                     "\n**blimp**: Battle Blimp"
                     "\n**slammer**: Stone Slammer"
                     "\n**barracks**: Siege Barracks"
                     "\n**launcher**: Log Launcher"
                     "\n**flinger**: Flame Flinger")
            embed.add_field(name="/siege <siege type>", value=siege, inline=False)
            embed.set_footer(icon_url="https://openclipart.org/image/300px/svg_to_png/122449/1298569779.png",
                             text="The Arborist proudly maintained by TubaKid.")
            return await interaction.send(embed=embed)
        if siege_req in ["ww", "wall wrecker", "ground"]:
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
        elif siege_req in ["log", "launcher", "log launcher", "ll"]:
            siege_name = "Log Launcher"
            thumb = "https://coc.guide/static/imgs/troop/siege-log-launcher.png"
        elif siege_req in ["flame", "flinger", "flame flinger", "ff"]:
            siege_name = "Flame Flinger"
            thumb = "https://coc.guide/static/imgs/troop/siege-catapult.png"
        else:
            return await interaction.response.send_message("You have provided an invalid siege machine type. "
                                                           "Please specify `ground`, `blimp`, `slammer`, `barracks`, "
                                                           "`launcher`, or `flinger`.")
        donors = []
        requestor = None
        # get requestor player tag from Discord ID
        clan = await self.bot.coc.get_clan("#CVCJR89")
        requestor_tag = await self.bot.links.get_linked_players(user_id)
        # Remove any links for player tags that aren't currently in Oak
        if len(requestor_tag) > 1:
            member_tags = [x.tag for x in clan.members]
            for tag in requestor_tag:
                if tag not in member_tags:
                    requestor_tag.remove(tag)
        # if still more than one, remove TH9 and below
        if len(requestor_tag) > 1:
            players = []
            for tag in requestor_tag:
                player = await self.bot.coc.get_player(tag)
                if player.town_hall >= 10:
                    players.append(player)
            # if still more than one, prompt user
            if len(players) > 1:
                view = ButtonView(players)
                await interaction.send(content="Please select the appropriate player", view=view)
                await view.wait()
                if view.value:
                    requestor_tag = view.value
                else:
                    # timed out, pick at random
                    requestor_tag = players[0].tag
        # confirm we are down to just a str
        if not isinstance(requestor_tag, str):
            requestor_tag = requestor_tag[0]
        # We should now have a single requestor tag to work with
        self.bot.logger.debug(f"SM Requestor Tag is {requestor_tag}")
        await interaction.response.send_message(f"Searching for clan members with a {siege_name}...")
        # find oak players with the requested siege machine
        async for player in clan.get_detailed_members():
            if siege_name in [troop.name for troop in player.siege_machines]:
                discord_id = await self.bot.links.get_link(player.tag)
                donors.append(f"{player.name}: <@{discord_id}>")
            if requestor_tag == player.tag:
                requestor = player.name
        if not requestor:
            requestor = interaction.user.display_name
        embed = nextcord.Embed(title=f"{siege_name} Request",
                               description=f"{requestor} has requested a {siege_name}",
                               color=0xb5000)
        embed.set_footer(icon_url=thumb, text="Remember to select your siege machine when you attack!")
        content = "**Potential donors include:**\n"
        content += "\n".join(donors)
        self.bot.logger.debug(content)
        await channel.send(embed=embed)
        await channel.send(content)

    @nextcord.slash_command(name="welcome",
                            description="Enter your player tag to gain access to the Discord server.",
                            guild_ids=[settings['discord']['oakguild_id'], settings['discord']['botlogguild_id']])
    async def welcome(self,
                      interaction: Interaction,
                      tag: str = SlashOption(description="Clash of Clans Player Tag",
                                             required=True)):
        member_role = interaction.guild.get_role(settings['oak_roles']['member'])
        for role in interaction.user.roles:
            if role == member_role:
                return await interaction.response.send_message("You already have the Member role.", ephemeral=True)
        try:
            player = await self.bot.coc.get_player(tag)
        except coc.NotFound:
            return await interaction.response.send_message("Bad player tag. Please try again.")
        if player.clan.tag != "#CVCJR89":
            return await interaction.response.send_message("That player is not currently in Reddit Oak.")
        await interaction.response.defer()
        # check to see if player tag is already linked to the Discord ID
        link_tags = await self.bot.links.get_linked_players(interaction.user.id)
        self.bot.logger.info(link_tags)
        match = False
        for link in link_tags:
            if link == player.tag:
                match = True
        if not match:
            # see if player tag is linked to a different Discord ID
            discord_id = await self.bot.links.get_link(player.tag)
            if discord_id:
                return await interaction.followup.send(f"Your player tag is linked to a different Discord ID. "
                                                       f"Our admin team will need to make adjustments.\n"
                                                       f"<@&{settings['oak_roles']['elder']}> "
                                                       f"<@&{settings['oak_roles']['co-leader']}>")
        if not match:
            await self.bot.links.add_link(player.tag, interaction.user.id)
        await interaction.user.add_roles(member_role)
        await interaction.user.edit(nick=player.name)
        town_hall_role = interaction.guild.get_role(settings['oak_roles'][f"TH{player.town_hall}"])
        await interaction.user.add_roles(town_hall_role)

    @commands.command(name="invite")
    async def invite(self, ctx):
        await ctx.send("https://discord.me/redditoak")

    @commands.command(name="next")
    async def _next(self, ctx):
        """Clan Capital Upgrade information. This command will respond with the next recommended
        upgrades for the Clan Capital."""
        # gc = gspread.service_account(filename="service_account.json")
        sheet = gc.open_by_key(settings['google']['capital_id'])
        sh = sheet.worksheet("Clan Capital Upgrades")
        values = sh.get("K4:L6")
        embed = nextcord.Embed(title="Clan Capital Upgrades",
                               description="Please use this as a guide for spending your Capital Gold",
                               color=nextcord.Color.dark_purple())
        for row in values:
            embed.add_field(name=row[0], value=row[1])
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(General(bot))
