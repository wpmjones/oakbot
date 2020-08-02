import discord
import re

from discord.ext import commands
from cogs.utils.constants import clans
from cogs.utils.models import WarData
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from config import settings, emojis


class Cwl(commands.Cog):
    """War bot commands and setup"""
    def __init__(self, bot):
        self.bot = bot

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




def setup(bot):
    bot.add_cog(Cwl(bot))
