import coc
import discord

from discord.ext import commands
from cogs.utils.constants import clans
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from config import settings


def breakdown(members, process=None):
    res = {}
    for m in members:
        th = m.town_hall if m.town_hall > 9 else 9
        if th not in res:
            res[th] = 0
        val = 1 if process is None else process(m)
        res[th] += val
    return "/".join(f"{res.get(th, 0)}" for th in range(13, 8, -1))


superscriptNumbers = u"⁰¹²³⁴⁵⁶⁷⁸⁹"


def sup(c):
    if ord('0') <= ord(c) <= ord('9'):
        return superscriptNumbers[ord(c) - ord('0')]
    else:
        return c


def th_super(s):
    s = str(s)
    ret = u""
    for c in s:
        ret += sup(c)
    return ret


def member_display(member):
    return f"{member.map_position}. {member.name}{th_super(member.town_hall)}"


class Cwl(commands.Cog):
    """War bot commands and setup"""
    def __init__(self, bot):
        self.bot = bot
        self.bot.coc.add_events(self.on_roster_change)

    def cog_unload(self):
        self.bot.coc.remove_events(self.on_roster_change)

    @commands.group(name="cwl", invoke_without_command=True)
    async def cwl(self, ctx, clan_name: str = "oak"):
        """CWL War Command
        Provides information on Clan War Leagues
        """
        if ctx.invoked_subcommand is not None:
            return

        if clan_name.lower() == "oak":
            clan_tag = clans['Reddit Oak']
        else:
            clan_tag = clans['Reddit Quercus']
        image = Image.open(f"images/oak-bg-1.jpg")
        font_24 = ImageFont.truetype("fonts/adam.otf", 24)
        font_36 = ImageFont.truetype("fonts/adam.otf", 36)
        group = await self.bot.coc.get_league_group(clan_tag)
        counter = 1
        x = 300
        y = 50
        draw = ImageDraw.Draw(image)
        async for war in group.get_wars():
            draw.rectangle([x, y, x+650, y+50], fill=(15, 15, 15))
            draw.text((x+10, y+12), f"{counter}. {war.clan.name}", fill=(250, 250, 250), font=font_36)
            draw.rectangle([x+700, y, x+1000, y+50], fill=(15, 15, 15))
            # Center
            text_width, text_height = draw.textsize(f"stars", font_36)
            center_x = (x + 850) - (text_width / 2)
            draw.text((center_x, y+12), f"stars", fill=(250, 250, 250), font=font_36)
            draw.rectangle([x+1050, y, x+1300, y+50], fill=(15, 15, 15))
            # Center
            text_width, text_height = draw.textsize(f"dest", font_36)
            center_x = (x + 1175) - (text_width / 2)
            draw.text((center_x, y+12), f"dest", fill=(250, 250, 250), font=font_36)
            counter += 1
            y += 65
        buffer = BytesIO()
        image.save(buffer, "png")
        buffer.seek(0)
        await ctx.send(file=discord.File(buffer, filename="cwl.png"))

    @coc.WarEvents.members(clans['Reddit Oak'])
    async def on_roster_change(self, old_war, new_war):
        member_list = []
        for member in new_war.opponent.members:
            member_list.append(member_display(member))
        elder_channel = self.bot.get_channel(settings['oak_channels']['elder_chat'])
        old_breakdown = breakdown(old_war.members)
        new_breakdown = breakdown(new_war.members)
        content = (f"**CWL Roster Change**\n"
                   f"Old Breakdown: {old_breakdown}\n"
                   f"New Breakdown: {new_breakdown}")
        await elder_channel.send("\n".join(member_list))


def setup(bot):
    bot.add_cog(Cwl(bot))
