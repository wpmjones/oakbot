import coc
import discord
import random

from discord.ext import commands
from config import settings


class MembersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.coc.add_events(self.on_clan_join,
                                self.on_clan_leave
                                )

    def cog_unload(self):
        self.bot.coc.remove_events(self.on_clan_join,
                                   self.on_clan_leave
                                   )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Discord listener which is called when a user joins the Discord server."""
        channel = member.guild.get_channel(251463913437134848)
        content = (f"Welcome to Reddit Oak's Discord Server {member.mention}! We're happy to have you! Please "
                   "change your Discord nickname to match your in game name so that we know who you are.  If you have "
                   "recently joined Reddit Oak, you must read our rules at https://www.reddit.com/r/coc_redditoak.  "
                   "There is a form at the end that you will need to complete before we can give you more roles on "
                   "this server.\n\nMost of the good talking will happen in <#299901545888219137>.  Please keep an eye "
                   "on <#530126055256883210> for important information.  <#362575004589752321> and "
                   "<#529404677440274472> are there for tracking purposes.  And <#529406479921446932> is available "
                   "for all your NSFW needs.  (Don't let it go too far.)\n\nIf you haven't already, we highly "
                   "recommend that you also join the Reddit Clan System Discord server!  "
                   "https://discord.gg/X8U9XjD\n\nHave fun!")
        await channel.send(content)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Discord listener which is called when a user leaves the Discord server."""
        # Build random list of messages
        msg_options = [" just left the server.  Buh Bye!", 
                       " just left our Discord. I wonder if we will miss them.",
                       " just left. What's up with that?"]
        channel = member.guild.get_channel(251463913437134848)
        content = member.display_name + random.choice(msg_options)
        await channel.send(content)

    @commands.command()
    @commands.guild_only()
    async def joined(self, ctx, *, member: discord.Member):
        """Says when a member joined."""
        await ctx.send(f"{member.display_name} joined on {member.joined_at}")

    @commands.command(name="perms", aliases=["perms_for", "permissions"])
    @commands.guild_only()
    async def check_permissions(self, ctx, *, member: discord.Member = None):
        """A simple command which checks a members Guild Permissions.
        If member is not provided, the author will be checked."""

        if not member:
            member = ctx.author

        # Here we check if the value of each permission is True.
        perms = "\n".join(perm for perm, value in member.guild_permissions if value)

        # And to make it look nice, we wrap it in an Embed.
        embed = discord.Embed(title="Permissions for:", description=ctx.guild.name, colour=member.colour)
        embed.set_author(icon_url=member.avatar_url, name=str(member))

        # \uFEFF is a Zero-Width Space, which basically allows us to have an empty field name.
        embed.add_field(name="\uFEFF", value=perms)

        await ctx.send(content=None, embed=embed)

    @coc.ClanEvents.member_join()
    async def on_clan_join(self, new_member, clan):
        """Things to do when a new player joins the clan"""
        self.bot.coc.add_player_updates(new_member.tag)

    @coc.ClanEvents.member_leave()
    async def on_clan_leave(self, old_member, clan):
        """Things to do when a player leaves the clan"""
        channel = self.bot.get_channel(settings['oak_channels']['member_status_chat'])
        await channel.send(f"{old_member.name} ({old_member.tag}) has left Reddit Oak. Maybe they'll be back. "
                           f"Maybe not! Just letting you know. It's not like I'm going to remove them or anything.")

def setup(bot):
    bot.add_cog(MembersCog(bot))
