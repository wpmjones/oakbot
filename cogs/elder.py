import discord
import pymssql
import requests
import asyncio
import asyncpg
from discord.ext import commands
from datetime import datetime, timedelta
from config import settings, color_pick, logger, emojis
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools


class Elder(commands.Cog):
    """Elder only Arborist commands"""
    def __init__(self, bot):
        self.bot = bot

    # TODO Add command for get DM history with @user arg

    @commands.command(name="elder", hidden=True)
    async def elder(self, ctx, command: str = "help"):
        """Help menu for elder staff"""
        if authorized(ctx.author.roles):
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
                embed.add_field(name="/warn remove #", value=warn_remove, inline=False)
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
            if command in ["help", "presence"]:
                presence = "Change the bot presence (message under bot name) to the default OR the specified message."
                embed.add_field(name="/presence <default or message>", value=presence, inline=False)
            await ctx.send(embed=embed)
            logger(ctx, "INFO", "elder", {"Request": command})
        else:
            logger(ctx, "WARNING", "elder", {"Request": command}, "User not authorized")
            await ctx.send("Wait a minute punk! You aren't allowed to use that command")

    @commands.command(name="war", aliases=["xar"], hidden=True)
    async def war(self, ctx, add, in_game_name, discord_id):
        if add == "add":
            is_user, user = is_discord_user(ctx.guild, int(discord_id))
            if is_user:
                if in_game_name.startswith("#"):
                    # working with player tag
                    pass

    @commands.command(name="giphy", hidden=True)
    async def giphy(self, ctx, gif_text):
        if ctx.author.is_on_mobile():
            await ctx.send("https://giphy.com/gifs/quality-mods-jif-6lt4syTAmvzAk")

    @commands.command(name="role", hidden=True)
    @commands.guild_only()
    async def role(self, ctx, player, role_name):
        """Command to add/remove roles from users"""
        if authorized(ctx.author.roles):
            # convert discord mention to user id only
            if player.startswith("<"):
                discord_id = "".join(player[2:-1])
                if discord_id.startswith("!"):
                    discord_id = discord_id[1:]
            else:
                await ctx.send(emojis['other']['redx'] + (" I don't believe that's a real Discord user. "
                                                          "Please make sure you are using the '@' prefix."))
                return
            # get role ID for specified role
            guild = ctx.bot.get_guild(settings['discord']['oakGuildId'])
            if role_name.lower() not in settings['oakRoles']:
                await ctx.send(emojis['other']['redx'] + (" I'm thinking you're going to have to provide "
                                                          "a role that is actually used in this server.\n"
                                                          "Try Guest, Member, Elder, or Co-Leader."))
                return
            role_obj = guild.get_role(int(settings['oakRoles'][role_name.lower()]))
            # test if has role, remove if has, else add
            is_user, user = is_discord_user(guild, int(discord_id))
            if not is_user:
                await ctx.send(emojis['other']['redx'] + f" User provided **{player}** "
                               f"is not a member of this discord server.")
                return
            flag = True
            for role in user.roles:
                if role.name.lower() == role_name.lower():
                    flag = False
            if flag:
                await user.add_roles(role_obj, reason=f"Arborist command issued by {ctx.author}")
                await ctx.send(f":white_check_mark: Changed roles for {user.display_name}, +{role_name}")
            else:
                await user.remove_roles(role_obj, reason=f"Arborist command issued by {ctx.author}")
                await ctx.send(f":white_check_mark: Changed roles for {user.display_name}, -{role_name}")
        else:
            logger(ctx, "WARNING", "elder", {"Player": player, "Role Name": role_name}, "User not authorized")
            await ctx.send("Wait a minute punk! You aren't allowed to use that command")

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
            conn = pymssql.connect(settings['database']['server'],
                                   settings['database']['username'],
                                   settings['database']['password'],
                                   settings['database']['database'])
            cursor = conn.cursor(as_dict=True)
            cursor.execute(f"SELECT tag, slackId FROM coc_oak_players WHERE playerName = '{player}'")
            fetched = cursor.fetchone()
            conn.close()
            if fetched is not None:
                discord_id = fetched['slackId']
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
                    url = (f"{settings['google']['oaktable']}?call=kick&rowNum={str(row_num)}&reason={reason}"
                           f"&ban={str(ban)}")
                    requests.get(url)
                    reason = reason.replace("%20", " ")
                    content = f"{player} has been moved to old members."
                    guild = ctx.bot.get_guild(settings['discord']['oakGuildId'])
                    is_user, user = is_discord_user(guild, int(discord_id))
                    # TODO else for is_user
                    # TODO add code to kick if ban
                    if is_user and ban == 0:
                        await user.remove_roles(guild.get_role(settings['oakRoles']['member']), reason=reason)
                        content += " Member role has been removed."
                    if is_user and ban == 1:
                        await user.kick(reason=reason)
                        content += f" {user.mention} kicked from server. If Discord ban is necessary, now is the time!"
                    logger(ctx, "INFO", "elder", {"Player": player, "Reason": reason})
                    await ctx.send(content)
                else:
                    logger(ctx, "WARNING", "elder", {"Player": player}, "Player not found in Oak Table.")
                    await ctx.send("Player name not found in Oak Table. Please try again.")
                    return
            else:
                logger(ctx, "WARNING", "elder", {"Player": player}, "Player not found in SQL Database.")
                await ctx.send("You have provided an invalid player name.  Please try again.")
                return
        else:
            logger(ctx, "WARNING", "elder", {"Player": player, "Reason": " ".join(reason)}, "User not authorized")
            await ctx.send("Wait a minute punk! You aren't allowed to use that command")

    @commands.command(name="warn", aliases=["warning", "watch"], hidden=True)
    async def warn(self, ctx, player: str = "list", *warning):
        """Command to add warnings for players
        /warn list (or just /warn) will show a list of all warnings
        To add a warning, use:
        /warn TubaKid This is a warning
        For names with spaces, use quotes:
        /warn "Professor Mahon" This is another warning
        To remove a warning, request the list first to obtain the warning ID.
        /warn remove #"""
        if authorized(ctx.author.roles):
            conn = pymssql.connect(settings['database']['server'],
                                   settings['database']['username'],
                                   settings['database']['password'],
                                   settings['database']['database'],
                                   autocommit=True)
            cursor = conn.cursor(as_dict=True)
            if player == "list" or player is None:
                cursor.execute("SELECT * FROM coc_oak_warnList ORDER BY playerName, strikeNum")
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
                logger(ctx, "INFO", "elder", {"Command": "List"})
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
                    logger(ctx, "DEBUG", "elder", {}, f"Awaited reaction {reaction} with user {user}")
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
                logger(ctx, "INFO", "elder",
                       {"Action": "Warning Removal", "Warning": fetched['warning'], "Player": fetched['playerName']})
                await sent_msg.edit(content=f"Warning **{fetched['warning']}** "
                                            f"removed for **{fetched['playerName']}**.")
            else:
                warning = " ".join(warning)
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
                    logger(ctx, "INFO", "elder", {"Player": player, "Warning": warning})
                else:
                    logger(ctx, "WARN", "elder", {"Player": player, "Warning": warning},
                           "Player name not found in SQL Database.")
                    await ctx.send("You have provided an invalid player name.  Please try again.")
                    return
                conn.close()
        else:
            logger(ctx, "WARNING", "elder", {"Player": player, "Warning": " ".join(warning)},
                   "User not authorized")
            await ctx.send("Wait a minute punk! You aren't allowed to use that command")

    @commands.command(name="unconfirmed", aliases=["un"], hidden=True)
    async def unconfirmed(self, ctx, *args):
        """Commands to deal with players who have not confirmed the rules
        list - Show members who have not confirmed the rules
        kick playername - Move specified player to No Confirmation
        move playername - Move specified player to Regular Members"""
        if authorized(ctx.author.roles):
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
                            url = (f"{settings['google']['oaktable']}?call=unconfirmed&command={arg}"
                                   f"&rowNum={str(row_num)}")
                            r = requests.get(url)
                            content = r.text
                            break
                        else:
                            row_num += 1
            else:
                logger(ctx, "WARNING", "elder", {"Args": " ".join(args)}, "Invalid argument from user.")
                content = "You have provided an invalid argument. Please specify `list`, `kick`, or `move`."
                await ctx.send(content)
                return
            logger(ctx, "INFO", ctx.command, args, content)
            await ctx.send(content)
        else:
            logger(ctx, "WARNING", "elder", {"Args": " ".join(args)}, "User not authorized")
            await ctx.send("Wait a minute punk! You aren't allowed to use that command")

    @commands.command(name="presence", hidden=True)
    async def presence(self, ctx, *, msg: str = "default"):
        """Command to modify bot presence"""
        if authorized(ctx.author.roles):
            if msg.lower() == "default":
                activity = discord.Game(" with fertilizer")
            else:
                activity = discord.Activity(type=discord.ActivityType.watching, name=msg)
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
            print(f"{datetime.now()} - {ctx.author} changed the bot presence to {msg}")
        else:
            logger(ctx, "WARNING", "elder", {"Presence": msg}, "User not authorized")
            await ctx.send("Wait one cotton pickin' minute jackrabbit! That command is not for you!")


def authorized(user_roles):
    for role in user_roles:
        if role.id in [settings['oakRoles']['elder'],
                       settings['oakRoles']['co-leader'],
                       settings['oakRoles']['leader']]:
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


scope = "https://www.googleapis.com/auth/spreadsheets.readonly"
spreadsheetId = settings['google']['oaktableId']
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
