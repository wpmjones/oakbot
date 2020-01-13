import discord
import asyncio
import season

from discord.ext import commands
from cogs.utils.db import Sql, Psql
from cogs.utils.checks import is_elder
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from config import settings, color_pick, emojis


class Elder(commands.Cog):
    """Elder only Arborist commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="elder", hidden=True)
    @is_elder()
    async def elder(self, ctx, command: str = "help"):
        """Help menu for elder staff"""
        embed = discord.Embed(title="Reddit Oak Elder Help Menu",
                              description="All the elder commands you need but can't remember how to use!",
                              color=color_pick(66, 134, 244))
        embed.add_field(name="Commands:", value="-----------", inline=True)
        if command in ["help", "role"]:
            role = ("Adds the specified role to the specified user if they do not have it. "
                    "Removes the role if they already have it.")
            embed.add_field(name="/role <@discord mention> <discord role>", value=role, inline=False)
        if command in ["help", "warn"]:
            warn_list = "Lists all strikes for all users. Sorted by user (alphabetically)."
            embed.add_field(name="/warn", value=warn_list, inline=False)
            warn_add = ("Adds a strike to the specified player with the specified reason. The bot will "
                        "respond with a list of all strikes for that player. No DM is sent at this time! "
                        "That will be a future enhancement. Please notify them in some other way.")
            embed.add_field(name="/warn <in-game name> <reason for warning>", value=warn_add, inline=False)
            warn_remove = ("Removes the specified warning (warning ID). You will need to do /warn list "
                           "first to obtain the warning ID.")
            embed.add_field(name="/warn remove <warning ID>", value=warn_remove, inline=False)
        if command in ["help", "kick"]:
            kick = ('Removes specified player from the Oak Table adding the reason you supply to the notes. '
                    'Removes the Member role from their Discord account. For players with spaces in '
                    'their name, "user quotes".')
            embed.add_field(name="/kick <in-game name> <reason for kick>", value=kick, inline=False)
        if command in ["help", "ban"]:
            ban = ("Removes specified player from the Oak Table adding the reason you "
                   "supply and flags them as a permanent ban. Kicks the player from the Discord server. "
                   "For players with spaces in their name, 'use quotes'.")
            embed.add_field(name="/ban <in-game name> <reason for ban>", value=ban, inline=False)
        if command in ["help", "unconfirmed"]:
            un_list = ("Lists all players who have not yet confirmed the rules. "
                       "If they have been in the clan for more than 2 days, you will see a :boot:")
            embed.add_field(name="/unconfirmed", value=un_list, inline=False)
            un_kick = "Move specified player to No Confirmation."
            embed.add_field(name="/unconfirmed kick <in-game name>", value=un_kick, inline=False)
            un_move = ("Move specified player to Regular Member "
                       "(if they failed the quiz or didn't move for some other reason.")
            embed.add_field(name="/unconfirmed move <in-game name>", value=un_move, inline=False)
        await ctx.send(embed=embed)
        self.bot.logger.info(f"{ctx.command} by {ctx.author} in {ctx.channel} | Request: {command}")

    @commands.command(name="war", aliases=["xar"])
    async def war(self, ctx, add, player_input, member: discord.Member):
        """This command mirrors the warbot command to link discord id to player tag
        Since the elders are already using the command, this snags the same line and
        uses the information to add records in the PostgreSQL database to link the same."""
        player_tag = ""
        if authorized(ctx.author.roles) and add == "add":
            if player_input.startswith("#"):
                player_tag = player_input[1:]
                print(player_tag)
            else:
                oak_tag = "#CVCJR89"
                try:
                    player = await self.bot.coc.get_player(f"#{player_input}")
                    if player.clan.tag == oak_tag:
                        player_tag = player_input
                        print(player_tag)
                except:
                    # Assume input provided is the player name
                    # members = await self.bot.coc.get_members(oak_tag)
                    members = (await self.bot.coc.get_clan(oak_tag)).members
                    try:
                        player_tag = members[[member.name for member in members].index(player_input)].tag[1:]
                        print(player_tag)
                    except:
                        print("fail")
                        self.bot.logger.info(f"{player_input} is not valid for the war add command."
                                             f"Attempted by {ctx.author} in {ctx.channel}.")
                        return
            await Psql(self.bot).link_user(player_tag, member.id)
            self.bot.logger.debug(f"Discord ID successfully added to db for {player_input}.")

    @war.error
    async def war_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            self.bot.logger.warning(f"{ctx.author} issued the /war command, but there was a problem "
                                    f"with the Discord user.")

    @commands.command(name="giphy", hidden=True)
    async def giphy(self, ctx, gif_text):
        if ctx.author.is_on_mobile():
            await ctx.send("https://giphy.com/gifs/quality-mods-jif-6lt4syTAmvzAk")

    @commands.command(name="role", hidden=True)
    @commands.guild_only()
    async def role(self, ctx, user: discord.Member, role_name):
        """Command to add/remove roles from users"""
        if authorized(ctx.author.roles):
            # get role ID for specified role
            guild = ctx.bot.get_guild(settings['discord']['oakguild_id'])
            if role_name.lower() not in settings['oak_roles']:
                await ctx.send(emojis['other']['redx'] + (" I'm thinking you're going to have to provide "
                                                          "a role that is actually used in this server.\n"
                                                          "Try Guest, Member, Elder, or Co-Leader."))
                return
            role_obj = guild.get_role(int(settings['oak_roles'][role_name.lower()]))
            flag = True
            # check to see if the user already has the role
            for role in user.roles:
                if role.name.lower() == role_name.lower():
                    flag = False
            if flag:
                await user.add_roles(role_obj, reason=f"Arborist command issued by {ctx.author}")
                content = f":white_check_mark: **Added** {role_name.title()} role for {user.display_name}"
                if role_name.lower() == "member":
                    content += "\nIs it also time to do `/war add`?"
                await ctx.send(content)
            else:
                await user.remove_roles(role_obj, reason=f"Arborist command issued by {ctx.author}")
                await ctx.send(f":white_check_mark: **Removed** {role_name.title()} role for {user.display_name}")
        else:
            self.bot.logger.warning(f"User not authorized - "
                                    f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                    f"Request: {role_name} for {user.discplay_name}")
            await ctx.send("Wait a minute punk! You aren't allowed to use that command")

    @role.error
    async def role_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("That is not a valid Discord user. Please try again.")

    @commands.command(name="kick", aliases=["ban"], hidden=True)
    async def kick(self, ctx, player, *reason):
        """Command to remove players from the clan.
        This will move member on the Oak Table to Old Members,
        add a reason if provided,
        and remove their Member role from Discord."""
        if authorized(ctx.author.roles):
            if ctx.command == "ban":
                ban = 1
            else:
                ban = 0
            with Sql(as_dict=True) as cursor:
                cursor.execute(f"SELECT tag, slackId FROM coc_oak_players WHERE playerName = %s", (player, ))
                fetched = cursor.fetchone()
            if fetched is not None:
                discord_id = fetched['slackId']
                player_tag = fetched['tag']
                if reason is not None:
                    reason = "%20".join(reason)
                else:
                    reason = ""
                result = sheet.values().get(spreadsheetId=spreadsheetId, range=currMemberRange).execute()
                values = result.get("values", [])
                row_num = 3
                found = 0
                for row in values:
                    if player.lower() == row[0].lower():
                        found = 1
                        break
                    else:
                        row_num += 1
                if found == 1:
                    # Make call to Google Sheet with info to perform move action
                    url = (f"{settings['google']['oak_table']}?call=kick&rowNum={str(row_num)}&reason={reason}"
                           f"&ban={str(ban)}")
                    async with ctx.session.get(url) as r:
                        if r.status != 200:
                            await ctx.send("Please check the Oak Table. Removal was not successful.")
                    reason = reason.replace("%20", " ")
                    content = f"{player} (#{player_tag}) has been moved to old members."
                    guild = ctx.bot.get_guild(settings['discord']['oakguild_id'])
                    is_user, user = is_discord_user(guild, int(discord_id))
                    # TODO else for is_user
                    if is_user and ban == 0:
                        await user.remove_roles(guild.get_role(settings['oak_roles']['member']), reason=reason)
                        content += " Member role has been removed."
                    if is_user and ban == 1:
                        await user.kick(reason=reason)
                        content += f" {user.mention} kicked from server. If Discord ban is necessary, now is the time!"
                    self.bot.logger.info(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                         f"{player} {ctx.command}ed for {reason}")
                    await ctx.send(content)
                else:
                    self.bot.logger.warning(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                            f"Problem: {player} not found in Oak Table")
                    return await ctx.send("Player name not found in Oak Table. Please try again.")
            else:
                self.bot.logger.warning(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                        f"Problem: {player} not found in SQL Database")
                return await ctx.send("You have provided an invalid player name.  Please try again.")
        else:
            self.bot.logger.warning(f"User not authorized - "
                                    f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                    f"Request: {player} was {ctx.command}ed for {reason}")
            await ctx.send("Wait a minute punk! You aren't allowed to use that command")

    @commands.command(name="warn", aliases=["warning", "warnings", "watch", "watchlist"], hidden=True)
    async def warn(self, ctx, player: str = "list", *warning):
        """Command to add warnings for players
        /warn list (or just /warn) will show a list of all warnings
        To add a warning, use:
        /warn TubaKid This is a warning
        For names with spaces, use quotes:
        /warn "Professor Mahon" This is another warning
        To remove a warning, request the list first to obtain the warning ID.
        /warn remove #"""
        # TODO Fix it so that apostrophes in the warning don't cause an error
        if authorized(ctx.author.roles):
            with Sql(as_dict=True) as cursor:
                if player == "list" or player is None:
                    cursor.execute("SELECT strikeNum, playerName, warnDate, warning, warningId "
                                   "FROM coc_oak_warnList "
                                   "ORDER BY playerName, strikeNum")
                    strikes = cursor.fetchall()
                    embed = discord.Embed(title="Reddit Oak Watchlist",
                                          description="All warnings expire after 60 days.",
                                          color=color_pick(181, 0, 0))
                    for strike in strikes:
                        strike_emoji = ":x:" * strike['strikeNum']
                        strike_text = (f"{strike['warning']}\nIssued on: {strike['warnDate']}\nWarning ID: "
                                       f"{str(strike['warningId'])}")
                        embed.add_field(name=f"{strike['playerName']} {strike_emoji}", value=strike_text, inline=False)
                    embed.set_footer(icon_url=("https://openclipart.org/image/300px/svg_to_png/109/"
                                               "molumen-red-round-error-warning-icon.png"),
                                     text="To remove a strike, use /warn remove <Warning ID>")
                    self.bot.logger.debug(f"{ctx.command} by {ctx.author} in {ctx.channel} | Request: List warnings")
                    await ctx.send(embed=embed)
                    return
                elif player == "remove":
                    reactions = [emojis['other']['upvote'], emojis['other']['downvote']]
                    cursor.execute(f"SELECT * FROM coc_oak_warnList WHERE warningId = {warning[0]}")
                    fetched = cursor.fetchone()
                    if fetched is None:
                        await ctx.send("No warning exists with that ID.  Please check the ID and try again.")
                        return
                    sent_msg = await ctx.send(f"Are you sure you want to remove {fetched['warning']} "
                                              f"from {fetched['playerName']}?")
                    await sent_msg.add_reaction(reactions[0][2:-1])
                    await sent_msg.add_reaction(reactions[1][2:-1])

                    def check(reaction, user):
                        return user == ctx.message.author and str(reaction.emoji) in reactions

                    try:
                        reaction, user = await ctx.bot.wait_for("reaction_add", timeout=60.0, check=check)
                        self.bot.logger.debug(f"Awaited reaction {reaction} with user {user}")
                    except asyncio.TimeoutError:
                        await sent_msg.edit(content="Removal cancelled because I'm feeling ignored. Don't ask me "
                                                    "to do things then ignore my questions.")
                    await sent_msg.clear_reactions()
                    if str(reaction.emoji) == reactions[1]:
                        await sent_msg.edit(content="Removal cancelled.  Maybe try again later if you feel up to it.")
                        return
                    elif str(reaction.emoji) == reactions[0]:
                        await sent_msg.edit(content="Removal in progress...")
                    else:
                        await sent_msg.edit(content="Something has gone horribly wrong and you're going to "
                                                    "have to talk to <@251150854571163648> about it. "
                                                    "Sorry. :frowning2: ")
                        return
                    cursor.execute(f"DELETE FROM coc_oak_warnings WHERE warningId = {warning[0]}")
                    self.bot.logger.debug(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                          f"Request: Removal of {fetched['warning']} for {fetched['playerName']}")
                    await sent_msg.edit(content=f"Warning **{fetched['warning']}** "
                                                f"removed for **{fetched['playerName']}**.")
                else:
                    warning = " ".join(warning)
                    warning.replace("'", "''")
                    cursor.execute(f"SELECT tag, slackId FROM coc_oak_players WHERE playerName = '{player}'")
                    fetched = cursor.fetchone()
                    if fetched is not None:
                        cursor.execute(f"INSERT INTO coc_oak_warnings (tag, warnDate, warning) "
                                       f"VALUES ('{fetched['tag']}', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}', "
                                       f"'{warning}')")
                        cursor.execute(f"SELECT * FROM coc_oak_warnList WHERE playerName = '{player}'")
                        strike_list = cursor.fetchall()
                        member = ctx.guild.get_member(int(fetched['slackId']))
                        await ctx.send("Warning added for " + player)
                        await member.send("Warning added!")
                        emoji = ":x:"
                        for strike in strike_list:
                            await ctx.send(emoji + " " + strike['warnDate'] + " - " + strike['warning'])
                            await member.send(f"{emoji} {strike['warnDate']} - {strike['warning']}")
                            emoji += ":x:"
                        self.bot.logger.debug(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                              f"Request: {player} warned for {warning}")
                    else:
                        self.bot.logger.warning(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                                f"Problem: {player} not found in SQL database | Warning: {warning}")
                        await ctx.send("You have provided an invalid player name.  Please try again.")
                        return
        else:
            self.bot.logger.warning(f"User not authorized - "
                                    f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                    f"Request: Warning for {player} for {' '.join(warning)}")
            await ctx.send("Wait a minute punk! You aren't allowed to use that command")

    @commands.command(name="stats", aliases=["stat", "check", "donations"], hidden=True)
    async def stats(self, ctx):
        """ Respond with those players not yet meeting attack/donation rules """
        if authorized(ctx.author.roles):
            msg = await ctx.send("Retreiving statistics. One moment please.")
            percent = season.get_days_since() / season.get_season_length()
            attacks_needed = int(20 * percent)
            donates_needed = int(600 * percent)
            clan = await self.bot.coc.get_clan("#CVCJR89")
            self.bot.logger.debug("Clan retrieved")
            warn_text = (f"**We are {season.get_days_since()} days into a {season.get_season_length()} day season.\n"
                         f"These statistics are based on what players should have this far into the season.**\n\n"
                         f"*TH9 or below*\n")
            low_text = high_text = ""
            async for player in clan.get_detailed_members():
                self.bot.logger.debug(f"Evaluating {player.name}")
                if player.town_hall <= 9 and player.attack_wins < attacks_needed:
                    low_text += (f"{player.name}{th_superscript(player.town_hall)} "
                                 f"is below {attacks_needed} attack wins ({player.attack_wins}).\n")
                elif player.town_hall >= 10 and player.donations < donates_needed:
                    high_text += (f"{player.name}{th_superscript(player.town_hall)} "
                                  f"is below {donates_needed} donations ({player.donations}).\n")
            warn_text += low_text
            warn_text += "\n\n*TH10 or above*\n"
            warn_text += high_text
            await msg.edit(content=warn_text)
        else:
            self.bot.logger.warning(f"User not authorized - "
                                    f"{ctx.command} by {ctx.author} in {ctx.channel}")
            await ctx.send("Wait a minute punk! You aren't allowed to use that command")

    @commands.command(name="unconfirmed", aliases=["un"], hidden=True)
    async def unconfirmed(self, ctx, *args):
        """Commands to deal with players who have not confirmed the rules
        list - Show members who have not confirmed the rules
        kick playername - Move specified player to No Confirmation
        move playername - Move specified player to Regular Members"""
        if authorized(ctx.author.roles):
            async with ctx.typing():
                if len(args) == 0:
                    arg = "list"
                else:
                    arg = args[0]
                result = sheet.values().get(spreadsheetId=spreadsheetId, range=newMemberRange).execute()
                values = result.get("values", [])
                if arg == "list":
                    # Set logging info
                    args = {"Argument": "List"}
                    if not values:
                        content = "No new members at this time."
                    else:
                        content = "**Unconfirmed new members:**"
                        for row in values:
                            content += "\n" + row[0] + " joined on " + row[3]
                            if (datetime.now() - timedelta(hours=6) - datetime.strptime(row[3], "%d-%b-%y")
                                    > timedelta(days=2)):
                                content += " :boot:"
                elif arg in ["kick", "move"]:
                    player_name = " ".join([x for x in args if x != arg])
                    # Set logging info
                    args = {"Argument": arg, "Player": player_name}
                    if not values:
                        content = "No new members at this time."
                    else:
                        # Set message if member not found. This will change in for loop if member is found.
                        content = "I had trouble finding that member.  Could you please try again?"
                        row_num = 57
                        for row in values:
                            if row[0] == player_name:
                                url = (f"{settings['google']['oak_table']}?call=unconfirmed&command={arg}"
                                       f"&rowNum={str(row_num)}")
                                async with ctx.session.get(url) as r:
                                    if r.status == 200:
                                        async for line in r.content:
                                            content = line.decode("utf-8")
                                break
                            else:
                                row_num += 1
                else:
                    self.bot.logger.warning(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                            f"Problem: Invalid arguments - {' '.join(args)}")
                    content = "You have provided an invalid argument. Please specify `list`, `kick`, or `move`."
                    await ctx.send(content)
                    return
                await ctx.send(content)
        else:
            self.bot.logger.warning(f"User not authorized - "
                                    f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                                    f"Request: {' '.join(args)}")
            await ctx.send("Wait a minute punk! You aren't allowed to use that command")


def authorized(user_roles):
    for role in user_roles:
        if role.id in [settings['oak_roles']['elder'],
                       settings['oak_roles']['co-leader'],
                       settings['oak_roles']['leader']]:
            return True
    return False


def is_discord_user(guild, discord_id):
    try:
        user = guild.get_member(discord_id)
        if user is None:
            return False, None
        else:
            return True, user
    except:
        return False, None


def sup(c):
    superscript_numbers = u"⁰¹²³⁴⁵⁶⁷⁸⁹"
    if ord('0') <= ord(c) <= ord('9'):
        return superscript_numbers[ord(c) - ord('0')]
    else:
        return c


# converts number to superscript
def th_superscript(s):
    s = str(s)
    ret = u""
    for c in s:
        ret += sup(c)
    return ret


scope = "https://www.googleapis.com/auth/spreadsheets.readonly"
spreadsheetId = settings['google']['oak_table_id']
currMemberRange = "Current Members!A3:A52"
newMemberRange = "Current Members!A57:D61"

store = file.Storage("token.json")
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets("credentials.json", scope)
    creds = tools.run_flow(flow, store)
service = build("sheets", "v4", http=creds.authorize(Http()), cache_discovery=False)
sheet = service.spreadsheets()


def setup(bot):
    bot.add_cog(Elder(bot))
