import discord, sys, traceback
from discord.ext import commands
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info('Starting bot')

description = '''Welcome to The Arborist - by TubaKid

All commands must begin with a slash'''

bot = commands.Bot(command_prefix='/', description=description, case_insensitive=True)
bot.remove_command('help')

@bot.event
async def on_ready():
  print('-------')
  print('Logged in as {0.user}'.format(bot))
  print('-------')

initialExtensions = ['cogs.general','cogs.members','cogs.elder','cogs.owner']

if __name__ == '__main__':
  for extension in initialExtensions:
    try:
      bot.load_extension(extension)
    except Exception as e:
      print('Failed to load extension {}'.format(extension), file=sys.stderr)
      traceback.print_exc()

bot.run(settings['discord']['oakbotToken'])
