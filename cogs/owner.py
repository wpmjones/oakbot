import traceback
import discord
from datetime import datetime
from discord.ext import commands


class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pull", hidden=True)
    @commands.is_owner()
    async def git_pull(self, ctx):
        """Command to pull latest updates from master branch on GitHub"""
        origin = self.bot.repo.remotes.origin
        try:
            origin.pull()
            print("Code successfully pulled from GitHub")
            await ctx.send("Code successfully pulled from GitHub")
        except Exception as e:
            print(f"ERROR: {type(e).__name__} - {e}")
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")

    @commands.command(name="close_db", aliases=["cdb", "cbd"], hidden=True)
    @commands.is_owner()
    async def close_db(self, ctx):
        """Command to close db connection before shutting down bot"""
        if self.bot.db.pool is not None:
            await self.bot.db.pool.close()
            await ctx.send("Database connection closed.")

    @commands.command()
    @commands.is_owner()
    async def log(self, ctx, num_lines: int = 10):
        with open(f"oakbot.log", "r") as f:
            list_start = -1 * num_lines
            await self.send_text(ctx.channel, "\n".join([line for line in f.read().splitlines()[list_start:]]))

    @log.error
    async def log_handler(self, ctx, error):
        """Listens for errors in log command"""
        tb_lines = traceback.format_exception(error.__class__, error, error.__traceback__)
        tb_text = "".join(tb_lines)
        self.bot.logger.exception(f"Exception found in {ctx.command}:\n{tb_text}")

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
