import discord
import gspread

from discord.ext import commands


class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="links", invoke_without_command=False)
    async def links(self, ctx):
        """[Group] For working with Links API
        ReverendMike is the man"""
        if ctx.invoked_subcommand is not None:
            return

    @links.command(name="add", hidden=True)
    async def links_add(self, ctx, player_tag, discord_id):
        """Add link to API Database

        /links add player_tag discord_id
        """
        try:
            await self.bot.links.add_link(player_tag, discord_id)
        except:
            return await ctx.send("Something broke. Link unsuccessful.")
        await ctx.send("Link added")

    @links.command(name="remove", aliases=["delete", "del", "rem"], hidden=True)
    async def links_remove(self, ctx, player_tag):
        """Remove link from API Database

        /links rem player_tag
        """
        try:
            await self.bot.links.delete_links(player_tag)
        except:
            return await ctx.send("Something broke. Removal unsuccessful.")
        await ctx.send("Link removed")

    @links.command(name="get", hidden=True)
    async def links_get(self, ctx, tag_or_id):
        """Testing coc.ext.discord_links

        /links get player_tag (must use #)
        /links get discord_id"""
        if tag_or_id.startswith("#"):
            # player_tag provided
            discord_id = await self.bot.links.get_link(tag_or_id)
            return await ctx.send(f"{tag_or_id} linked to {discord_id}.")
        else:
            # assume we have a discord_id
            tags = await self.bot.links.get_linked_players(tag_or_id)
            return await ctx.send(f"{tag_or_id} linked to {', '.join(tags)}.")

    @commands.command(name="gspread", hidden=True)
    @commands.is_owner()
    async def gspread(self, ctx):
        gc = gspread.oauth()
        sh = gc.open("Oak Table")
        await ctx.send(f"Success!  A3 = {sh.sheet1.get('A3')}")

    @commands.command(name="clear", hidden=True)
    @commands.is_owner()
    async def clear(self, ctx, num_msgs):
        async for message in ctx.channel.history(limit=num_msgs):
            await message.delete()
        await ctx.send(f"{num_msgs} message(s) deleted", delete_after=10)

    @commands.command(name="presence", hidden=True)
    @commands.is_owner()
    async def presence(self, ctx, *, msg: str = "default"):
        """Command to modify bot presence"""
        if msg.lower() == "default":
            activity = discord.Game(" with fertilizer")
        else:
            activity = discord.Activity(type=discord.ActivityType.watching, name=msg)
        await self.bot.change_presence(status=discord.Status.online, activity=activity)

    async def send_text(self, channel, text, block=None):
        """ Sends text ot channel, splitting if necessary """
        if len(text) < 2000:
            if block:
                await channel.send(f"```{text}```")
            else:
                await channel.send(text)
        else:
            coll = ""
            for line in text.splitlines(keepends=True):
                if len(coll) + len(line) > 1994:
                    # if collecting is going to be too long, send  what you have so far
                    if block:
                        await channel.send(f"```{coll}```")
                    else:
                        await channel.send(coll)
                    coll = ""
                coll += line
            await channel.send(coll)


def setup(bot):
    bot.add_cog(OwnerCog(bot))
