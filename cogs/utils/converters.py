import re
from datetime import datetime
from loguru import logger
from discord.ext import commands


class DateConverter(commands.Converter):
    """Convert user input into standard format date (YYYY-MM-DD)"""
    async def convert(self, ctx, argument):
        year_options = (f'{datetime.today().year}|{datetime.today().year+1}|'
                        f'{str(datetime.today().year)[2:]}|{str(datetime.today().year+1)[2:]}')

        # Check for text based month with day first
        pattern = (r'(?P<Date>\d+)[\s ]+'
                   r'(?P<Month>Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|'
                   r'Jul(y)?|Aug(ust)?|Sep(tember)?|Sept|Oct(ober)?|Nov(ember)?|Dec(ember)?)[\s ]+'
                   r'(?P<Year>' + year_options + ')')
        match = re.match(pattern, argument, re.IGNORECASE)
        if match:
            date_string = f"{match.group('Year')} {match.group('Month')[:3]} {match.group('Date')}"
            try:
                if len(match.group('Year')) == 2:
                    return datetime.strptime(date_string, '%y %b %d')
                else:
                    return datetime.strptime(date_string, '%Y %b %d')
            except ValueError:
                logger.error(f"{ctx.author} provided {argument}")
                raise commands.BadArgument(
                    'You may think that\'s a date, but I don\'t. Try using the YYYY-MM-DD format.')

        # Check for text based month with month first (optional comma)
        pattern = (r'(?P<Month>Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|'
                   r'Jul(y)?|Aug(ust)?|Sep(tember)?|Sept|Oct(ober)?|Nov(ember)?|Dec(ember)?)[\s ]+'
                   r'(?P<Date>\d+),?[\s ]+'
                   r'(?P<Year>' + year_options + ')')
        match = re.match(pattern, argument, re.IGNORECASE)
        if match:
            date_string = f"{match.group('Year')} {match.group('Month')[:3]} {match.group('Date')}"
            try:
                if len(match.group('Year')) == 2:
                    return datetime.strptime(date_string, '%y %b %d')
                else:
                    return datetime.strptime(date_string, '%Y %b %d')
            except ValueError:
                logger.error(f"{ctx.author} provided {argument}")
                raise commands.BadArgument(
                    'You may think that\'s a date, but I don\'t. Try using the YYYY-MM-DD format.')

        # Check for text based month with month last
        pattern = (r'(?P<Year>' + year_options + r')[\s ]+'
                   r'(?P<Date>\d+),?[\s ]+'
                   r'(?P<Month>Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|'
                   r'Jul(y)?|Aug(ust)?|Sep(tember)?|Sept|Oct(ober)?|Nov(ember)?|Dec(ember)?)')
        match = re.match(pattern, argument, re.IGNORECASE)
        if match:
            date_string = f"{match.group('Year')} {match.group('Month')[:3]} {match.group('Date')}"
            try:
                if len(match.group('Year')) == 2:
                    return datetime.strptime(date_string, '%y %b %d')
                else:
                    return datetime.strptime(date_string, '%Y %b %d')
            except ValueError:
                logger.error(f"{ctx.author} provided {argument}")
                raise commands.BadArgument(
                    'You may think that\'s a date, but I don\'t. Try using the YYYY-MM-DD format.')

        # Check for dates with year at the end
        pattern = r'(\d{1,2})[/ -.]?(\d{1,2})[/ -.]?(?P<Year>' + year_options + ')'
        logger.debug(pattern)
        match = re.match(pattern, argument, re.IGNORECASE)
        if match:
            if match.group(1) == match.group(2):
                date = month = match.group(1)
            elif int(match.group(1)) > 12:
                date = match.group(1)
                month = match.group(2)
            else:
                month = match.group(1)
                date = match.group(2)
            year = match.group('Year')
            logger.debug(year)

        # Check for dates with year at the beginning (then assume MM-DD)
        pattern = r'(?P<Year>' + year_options + r')[/ -.]?(?P<Month>\d{1,2})[/ -.]?(?P<Date>\d{1,2})'
        logger.debug(pattern)
        match = re.match(pattern, argument, re.IGNORECASE)
        if match:
            date = match.group('Date')
            month = match.group('Month')
            year = match.group('Year')

        try:
            date_string = f"{year} {month} {date}"
            if len(year) == 2:
                return datetime.strptime(date_string, '%y %m %d')
            else:
                return datetime.strptime(date_string, '%Y %m %d')
        except (ValueError, NameError):
            logger.error(f"{ctx.author} provided {argument}")
            raise commands.BadArgument(
                'You may think that\'s a date, but I don\'t. Try using the YYYY-MM-DD format.')

