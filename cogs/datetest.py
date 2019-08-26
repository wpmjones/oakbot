from discord.ext import commands
from cogs.utils.converters import DateConverter


class DateTest(commands.Cog):
    """For testing date input from user"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="dt")
    async def new_date(self, ctx, *, dt: DateConverter):
        await ctx.send(f"The provided date was converted to {dt}")


def setup(bot):
    bot.add_cog(DateTest(bot))
