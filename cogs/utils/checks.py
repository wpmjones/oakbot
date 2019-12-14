from discord.ext import commands


def not_zs():
    async def pred(ctx):
        return ctx.author.id != 302213800910782465
    return commands.check(pred)
