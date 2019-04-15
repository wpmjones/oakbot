import discord
import pymssql
import requests
from discord.ext import commands
from datetime import datetime, timedelta
from config import settings, color_pick, bot_log, emojis
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

class Elder:
    """Elder only Arborist commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="elder", hidden=True)
    async def elder(self, ctx, command: str = "help"):
        """Help menu for elder staff"""
        if authorized(ctx.author.roles):
            embed = discord.Embed(title = "Reddit Oak Elder Help Menu", description = "All the elder commands you need but can't remember how to use!", color = color_pick(66,134,244))
            embed.add_field(name = "Commands:", value = "-----------", inline = True)
            if command in ["help","role"]:
                role = "Adds the specified role to the specified user if they do not have it. Removes the role if they already have it."
                embed.add_field(name = "/role <@discord mention> <discord role>", value = role, inline = False)
            if command in ["help","warn"]:
                warnList = "Lists all strikes for all users. Sorted by user (alphabetically)."
                embed.add_field(name = "/warn", value = warnList, inline = False)
                warnAdd = "Adds a strike to the specified player with the specified reason. The bot will respond with a list of all strikes for that player. No DM is sent at this time! That will be a future enhancement. Please notify them in some other way."
                embed.add_field(name = "/warn <in-game name> <reason for warning>", value = warnAdd, inline = False)
                warnRemove = "Removes the specified warning (warning ID). You will need to do /warn list first to obtain the warning ID."
                embed.add_field(name = "/warn remove #", value = warnRemove, inline = False)
            if command in ["help","kick"]:
                kick = 'Removes specified player from the Oak Table adding the reason you supply to the notes. Removes the Member role from their Discord account. For players with spaces in their name, "user quotes".'
                embed.add_field(name = "/kick <in-game name> <reason for kick>", value = kick, inline = False)
            if command in ["help","ban"]:
                ban = 'Removes specified player from the Oak Table adding the reason you supply and flags them as a permanent ban. Kicks the player from the Discord server. For players with spaces in their name, "user quotes".'
                embed.add_field(name = "/ban <in-game name> <reason for ban>", value = ban, inline = False)
            if command in ["help", "unconfirmed"]:
                unList = "Lists all players who have not yet confirmed the rules. If they have been in the clan for more than 2 days, you will see a :boot:"
                embed.add_field(name = "/unconfirmed", value = unList, inline = False)
                unKick = "Move specified player to No Confirmation."
                embed.add_field(name = "/unconfirmed kick <in-game name>", value = unKick, inline = False)
                unMove = "Move specified player to Regular Member (if they failed the quiz or didn't move for some other reason."
                embed.add_field(name = "/unconfirmed move <in-game name>", value = unMove, inline = False)
            if command in ["help", "presence"]:
                presence = "Change the bot presence (message under bot name) to the default OR the specified message."
                embed.add_field(name = "/presence <default or message>", value = presence, inline = False)
            await ctx.send(embed = embed)
        else:
            print(bot_log(ctx.command,command,ctx.author,ctx.channel,1))
            await ctx.send("Wait a minute punk! You aren't allowed to use that command")

    @commands.command(name="giphy", hidden=True)
    async def giphy(self, ctx, gifText):
        if ctx.author.is_on_mobile():
           print(bot_log(ctx.command,gifText,ctx.author,ctx.channel))
           await ctx.send("https://giphy.com/gifs/quality-mods-jif-6lt4syTAmvzAk")

    @commands.command(name="role", hidden=True)
    @commands.guild_only()
    async def role(self, ctx, player, roleName):
        """Command to add/remove roles from users"""
        if authorized(ctx.author.roles):
            # convert discord mention to user id only
            if player.startswith("<"):
                discordId = "".join(player[2:-1])
                if discordId.startswith("!"):
                    discordId = discordId[1:]
            else:
                await ctx.send(emojis['other']['redx'] + " I don't believe that's a real Discord user. Please make sure you are using the '@' prefix.")
                return
            # get role ID for specified role
            guild = ctx.bot.get_guild(settings['discord']['oakGuildId'])
            if roleName.lower() not in settings['oakRoles']:
                await ctx.send(emojis['other']['redx'] + " I'm thinking you're going to have to provide a role that is actually used in this server.\nTry Guest, Member, Elder, or Co-Leader.")
                return
            roleObj = guild.get_role(int(settings['oakRoles'][roleName.lower()]))
            # test if has role, remove if has, else add
            isUser, user = isDiscordUser(guild, int(discordId))
            if isUser == False:
                await ctx.send(emojis['other']['redx'] + f" User provided **{player}** is not a member of this discord server.")
                return
            flag = True
            for role in user.roles:
                if role.name.lower() == roleName.lower():
                    flag = False
            if flag:
                await user.add_roles(roleObj, reason = f"Arborist command issued by {ctx.author}")
                await ctx.send(f":white_check_mark: Changed roles for {user.display_name}, +{roleName}")
            else:
                await user.remove_roles(roleObj, reason = f"Arborist command issued by {ctx.author}")
                await ctx.send(f":white_check_mark: Changed roles for {user.display_name}, -{roleName}")
        else:
            print(bot_log(ctx.command,player,ctx.author,ctx.channel,1))
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
            conn = pymssql.connect(settings['database']['server'], settings['database']['username'], settings['database']['password'], settings['database']['database'])
            cursor = conn.cursor(as_dict=True)
            cursor.execute(f"SELECT tag, slackId FROM coc_oak_players WHERE playerName = '{player}'")
            fetched = cursor.fetchone()
            conn.close()
            if fetched is not None:
                discordId = fetched['slackId']
                if reason is not None:
                    reason = "%20".join(reason)
                else:
                    reason = ""
                result = sheet.values().get(spreadsheetId=spreadsheetId, range=currMemberRange).execute()
                values = result.get("values", [])
                rowNum = 3
                found = 0
                for row in values:
                    if player.lower() == row[0].lower():
                        found = 1
                        break
                    else:
                        rowNum += 1
                if found == 1:
                    # Make call to Google Sheet with info to perform move action
                    url = settings['google']['oaktable'] + "?call=kick&rowNum=" + str(rowNum) + "&reason=" + reason + "&ban=" + str(ban)
                    r = requests.get(url)
                    content = f"{player} has been moved to old members."
                    guild = ctx.bot.get_guild(settings['discord']['oakGuildId'])
                    isUser, user = isDiscordUser(guild, int(discordId))
                    # else for isUser
                    # add code to kick if ban
                    if isUser == True and ban == 0:
                        await user.remove_roles(guild.get_role(512051408925884436), reason=reason)
                        content += " Member role has been removed."
                    print(bot_log(ctx.command,player,ctx.author,ctx.channel))
                    await ctx.send(content)
                else:
                    print(bot_log(ctx.command,player,ctx.author,ctx.channel,1))
                    await ctx.send("Player name not found in Oak Table. Please try again.")
                    return
            else:
                print(bot_log(ctx.command,player,ctx.author,ctx.channel,1))
                await ctx.send("You have provided an invalid player name.  Please try again.")
                return
        else:
            print(bot_log(ctx.command,player,ctx.author,ctx.channel,1))
            await ctx.send("Wait a minute punk! You aren't allowed to use that command")

    @commands.command(name="warn", aliases=["warning","watch"], hidden=True)
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
            conn = pymssql.connect(settings['database']['server'], settings['database']['username'], settings['database']['password'], settings['database']['database'], autocommit=True)
            cursor = conn.cursor(as_dict=True)
            if player == "list" or player is None:
                cursor.execute("SELECT * FROM coc_oak_warnList ORDER BY playerName, strikeNum")
                strikes = cursor.fetchall()
                embed = discord.Embed(title = "Reddit Oak Watchlist", description = "All warnings expire after 60 days.", color = color_pick(181,0,0))
                strikeList = ""
                for strike in strikes:
                    strikeEmoji = ":x:" * strike['strikeNum']
                    strikeText = strike['warning'] + "\nIssued on: " + strike['warnDate'] + "\nWarning ID: " + str(strike['warningId'])
                    embed.add_field(name = f"{strike['playerName']} {strikeEmoji}", value = strikeText, inline = False)
                embed.set_footer(icon_url = "https://openclipart.org/image/300px/svg_to_png/109/molumen-red-round-error-warning-icon.png", text = "To remove a strike, use /warn remove <Warning ID>")
                print(bot_log("list","warnings",ctx.author,ctx.channel))
                await ctx.send(embed=embed)
                return
            elif player == "remove":
                reactions = [emojis['other']['upvote'],emojis['other']['downvote']]
                cursor.execute(f"SELECT * FROM coc_oak_warnList WHERE warningId = {warning[0]}")
                fetched = cursor.fetchone()
                if fetched is None:
                    await ctx.send("No warning exists with that ID.  Please check the ID and try again.")
                    return
                sentMsg = await ctx.send(f"Are you sure you want to remove {fetched['warning']} from {fetched['playerName']}?")
                await sentMsg.add_reaction(reactions[0][2:-1])
                await sentMsg.add_reaction(reactions[1][2:-1])

                def check(reaction, user):
                    return user == ctx.message.author and str(reaction.emoji) in reactions

                try:
                    reaction, user = await ctx.bot.wait_for("reaction_add", timeout=60.0, check=check)
                except asyncio.TimeoutError:
                    await sentMsg.edit(content = "Removal cancelled because I'm feeling ignored. Don't ask me to do things then ignore my questions.")
                print(f"Awaited reaction {reaction} with user {user}")
                await sentMsg.clear_reactions()
                if str(reaction.emoji) == reactions[1]:
                    await sentMsg.edit(content = "Removal cancelled.  Maybe try again later if you feel up to it.")
                    return
                elif str(reaction.emoji) == reactions[0]:
                    await sentMsg.edit(content = "Removal in progress...")
                else:
                    await sentMsg.edit(content = "Something has gone horribly wrong and you're going to have to talk to <@251150854571163648> about it.  Sorry. :frowning2: ")
                    return
                cursor.execute(f"DELETE FROM coc_oak_warnings WHERE warningId = {warning[0]}")
                print(bot_log("Warning Removal",f"Warning: {fetched['warning']}. Player: {fetched['playerName']}",ctx.author,ctx.channel))
                await sentMsg.edit(content = f"Warning **{fetched['warning']}** removed for **{fetched['playerName']}**.")
            else:
                warning = " ".join(warning)
                cursor.execute(f"SELECT tag, slackId FROM coc_oak_players WHERE playerName = '{player}'")
                fetched = cursor.fetchone()
                if fetched is not None:
                    cursor.execute(f"INSERT INTO coc_oak_warnings (tag, warnDate, warning) VALUES ('{fetched['tag']}', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}', '{warning}')")
                    cursor.execute(f"SELECT * FROM coc_oak_warnList WHERE playerName = '{player}'")
                    strikeList = cursor.fetchall()
                    print(bot_log("Add warning",player,ctx.author,ctx.channel))
                    member = ctx.guild.get_member(int(fetched['slackId']))
                    await ctx.send("Warning added for " + player)
                    await member.send("Warning added!")
                    emoji = ":x:"
                    for strike in strikeList:
                        await ctx.send(emoji + " " + strike['warnDate'] + " - " + strike['warning'])
                        await member.send(f"{emoji} {strike['warnDate']} - {strike['warning']}")
                        emoji += ":x:"
                else:
                    print(bot_log(ctx.command,player,ctx.author,ctx.channel,1))
                    await ctx.send("You have provided an invalid player name.  Please try again.")
                    return
                conn.close()
        else:
            print(bot_log(ctx.command,player,ctx.author,ctx.channel,1))
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
                if not values:
                    content = "No new members at this time."
                else:
                    content = "**Unconfirmed new members:**"
                    for row in values:
                        content += "\n" + row[0] + " joined on " + row[3]
                        if datetime.now() - timedelta(hours=6) - datetime.strptime(row[3], "%d-%b-%y") > timedelta(days=2):
                            content += " :boot:"
            elif arg in ["kick","move"]:
                playerName = " ".join([x for x in args if x != arg])
                if not values:
                    content = "No new members at this time."
                else:
                    content = "I had trouble finding that member.  Could you please try again?"
                    rowNum = 57
                    for row in values:
                        if row[0] == playerName:
                            url = settings['google']['oaktable'] + "?call=unconfirmed&command=" + arg + "&rowNum=" + str(rowNum)
                            r = requests.get(url)
                            content = r.text
                            break
                        else:
                            rowNum += 1
            else:
                print(bot_log(ctx.command,arg,ctx.author,ctx.channel,1))
                content = "You have provided an invalid argument. Please specify `list`, `kick`, or `move`."
                return
            print(bot_log(ctx.command,arg,ctx.author,ctx.channel))
            await ctx.send(content)
        else:
            print(bot_log(ctx.command, args[0],ctx.author,ctx.channel,1))
            await ctx.send("Wait a minute punk! You aren't allowed to use that command")

    @commands.command(name="presence", hidden=True)
    async def presence(self, ctx, *, msg: str = "x"):
        """Command to modify bot presence"""
        if authorized(ctx.author.roles):
            if msg.lower() == "default":
                activity = discord.Game(" with fertilizer")
            else:
                activity = discord.Activity(type = discord.ActivityType.watching, name=msg)
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
            print(f"{datetime.now()} - {ctx.author} changed the bot presence to {msg}")
        else:
            print(bot_log(ctx.command,msg,ctx.author,ctx.channel,1))
            await ctx.send("Wait one cotton pickin' minute jackrabbit! That command is not for you!")

def authorized(userRoles):
    for role in userRoles:
        if role.name in ["Elder","Co-leader","Leader"]:
            return True
    return False

def isDiscordUser(guild, discordId):
    try:
        user = guild.get_member(discordId)
        if user == None:
            return False, None
        else:
            return True, user
    except:
        return False, None

def splitString(string, prepend="", append=""):
    messageLimit = 2000
    if len(string) <= 2000:
        return string, ""
    else:
        splitIndex = string.rfind("\n",0,messageLimit-len(prepend)-len(append))
        string1 = string[:splitIndex] + append
        string2 = prepend + string[splitIndex:]
        return string1, string2

scope = "https://www.googleapis.com/auth/spreadsheets.readonly"
spreadsheetId = "1BtA43_OR4Kzpx8XhrVXIrCvTkmIfb6RGvO42_OfYJNA"
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
