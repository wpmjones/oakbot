import re
import coc

from datetime import datetime
from cogs.utils.constants import clans
from discord.ext import commands

tag_validator = re.compile("^#?[PLYQGRJCUV0289]+$")


class PlayerConverter(commands.Converter):
    async def convert(self, ctx, argument):
        if isinstance(argument, coc.Player):
            return argument

        tag = coc.utils.correct_tag(argument)
        name = argument.strip()

        if tag_validator.match(tag):
            try:
                return await ctx.coc.get_player(tag)
            except coc.NotFound:
                raise commands.BadArgument("Looks like you provided a tag, but there are no players with that tag. "
                                           "Care to try again?")

        for clan_tag in clans.values():
            clan = await ctx.coc.get_clan(clan_tag)
            if clan.name == name or clan.tag == tag:
                raise commands.BadArgument(f"You appear to be passing the clan tag/name for `{clan.name}`")
            member = clan.get_member_by(name=name)
            if member:
                return member

        raise commands.BadArgument(f"Invalid tag or IGN. Please try again")


class ClanConverter(commands.Converter):
    async def convert(self, ctx, argument):
        if isinstance(argument, coc.BasicClan):
            return argument

        tag = coc.utils.correct_tag(argument)
        name = argument.strip().lower()
        clans = {
            "oak": "CVCJR89",
            "reddit oak": "CVCJR89",
            "quercus": "GVCPPG98",
            "reddit quercus": "GVCPPG98",
        }

        # If tag is valid, use the tag
        if tag_validator.match(tag):
            try:
                if tag[1:] in clans.values():
                    clan = await ctx.coc.get_clan(tag)
                else:
                    raise commands.BadArgument(f"{tag} is not a valid RCS clan.")
            except coc.NotFound:
                raise commands.BadArgument(f"{tag} is not a valid clan tag.")

            if clan:
                return clan

            raise commands.BadArgument(f'{tag} is not a valid clan tag.')

        # If no valid tag, try working with the name
        if name in clans.keys():
            tag = "#" + clans[name]
        else:
            raise commands.BadArgument(f"{name} is not a valid RCS clan.")

        try:
            clan = await ctx.coc.get_clan(tag)
        except coc.NotFound:
            raise commands.BadArgument(f"{tag} is not a valid clan tag.")

        if clan:
            return clan

        raise commands.BadArgument(f'Clan name or tag `{argument}` not found')


class DateConverter(commands.Converter):
    """Convert user input into standard format date (YYYY-MM-DD)"""

    async def convert(self, ctx, argument):
        error_msg = 'You may think that\'s a date, but I don\'t. Try using the DD-MM-YYYY format.'
        year_options = (f'{datetime.today().year}|{datetime.today().year + 1}|'
                        f'{str(datetime.today().year)[2:]}|{str(datetime.today().year + 1)[2:]}')

        # Check for text based month with day first
        pattern = (r'(?P<Date>\d{1,2})[/.\- ]'
                   r'(?P<Month>Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|'
                   r'Jul(y)?|Aug(ust)?|Sep(tember)?|Sept|Oct(ober)?|Nov(ember)?|Dec(ember)?)[/.\- ]'
                   r'(?P<Year>' + year_options + ')')
        match = re.match(pattern, argument, re.IGNORECASE)
        if match:
            date_string = f"{match.group('Year')} {match.group('Month')[:3]} {match.group('Date')}"
            if len(match.group('Year')) == 2:
                fmt = '%y %b %d'
            else:
                fmt = '%Y %b %d'

        # Check for text based month with month first
        pattern = (r'(?P<Month>Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|'
                   r'Jul(y)?|Aug(ust)?|Sep(tember)?|Sept|Oct(ober)?|Nov(ember)?|Dec(ember)?)[/.\- ]'
                   r'(?P<Date>\d{1,2})[/.\- ]'
                   r'(?P<Year>' + year_options + ')')
        match = re.match(pattern, argument, re.IGNORECASE)
        if match:
            date_string = f"{match.group('Year')} {match.group('Month')[:3]} {match.group('Date')}"
            if len(match.group('Year')) == 2:
                fmt = '%y %b %d'
            else:
                fmt = '%Y %b %d'

        # Check for YYYY-MM-DD
        pattern = (r'(?P<Year>' + year_options + r')[/.\- ](?P<Month>\d{1,2})[/.\- ](?P<Date>\d{1,2})')
        match = re.match(pattern, argument, re.IGNORECASE)
        if match:
            date_string = f"{match.group('Year')} {match.group('Month')} {match.group('Date')}"
            if len(match.group('Year')) == 2:
                fmt = '%y %m %d'
            else:
                fmt = '%Y %m %d'

        # Check for DD-MM-(YY)YY
        pattern = (r'(?P<Date>\d{1,2})[/.\- ](?P<Month>\d{1,2})[/.\- ](?P<Year>' + year_options + ')')
        match = re.match(pattern, argument, re.IGNORECASE)
        if match:
            date_string = f"{match.group('Year')} {match.group('Month')} {match.group('Date')}"
            if len(match.group('Year')) == 2:
                fmt = '%y %m %d'
            else:
                fmt = '%Y %m %d'

        try:
            return datetime.strptime(date_string, fmt)
        except (ValueError, NameError):
            raise commands.BadArgument(error_msg)

