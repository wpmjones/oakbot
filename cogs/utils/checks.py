from nextcord.ext import commands
from config import settings


def not_zs():
    async def pred(ctx):
        return ctx.author.id != 302213800910782465
    return commands.check(pred)


def check_is_elder(ctx):
    oak_guild = ctx.bot.get_guild(settings['discord']['oakguild_id'])
    elder = oak_guild.get_role(settings['oak_roles']['elder'])
    co = oak_guild.get_role(settings['oak_roles']['co-leader'])
    leader = oak_guild.get_role(settings['oak_roles']['leader'])
    oak_member = oak_guild.get_member(ctx.author.id)
    if not oak_member or not oak_member.roles:
        return False
    if elder in oak_member.roles or co in oak_member.roles or leader in oak_member.roles:
        return True
    else:
        return False


def is_elder():
    def pred(ctx):
        return check_is_elder(ctx)
    return commands.check(pred)
