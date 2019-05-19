import traceback
import git
import os
import coc
import asyncio
from loguru import logger
from discord.ext import commands
from config import settings
from oakdb import OakDB

enviro = "LIVE"

if enviro == "LIVE":
    token = settings['discord']['oakbotToken']
    prefix = "/"
    log_level = "INFO"
    coc_names = "vps"
else:
    token = settings['discord']['testToken']
    prefix = ">"
    log_level = "DEBUG"
    coc_names = "dev"

logger.add("oakbot.log", rotation="100MB", level=log_level)

description = """Welcome to The Arborist - by TubaKid

All commands must begin with a slash"""

bot = commands.Bot(command_prefix=prefix, description=description, case_insensitive=True)


@bot.event
async def on_ready():
    logger.info("-------")
    logger.info(f"Logged in as {bot.user}")
    logger.info("-------")
    bot.test_channel = bot.get_channel(settings['oakChannels']['testChat'])
    await bot.test_channel.send("The Arborist is now planting trees")


@bot.event
async def on_resumed():
    logger.info('resumed...')

initialExtensions = ["cogs.general",
                     "cogs.members",
                     "cogs.elder",
                     "cogs.owner",
                     "cogs.warrole",
                     ]

if __name__ == "__main__":
    bot.remove_command("help")
    bot.repo = git.Repo(os.getcwd())
    bot.db = OakDB(bot)
    loop = asyncio.get_event_loop()
    pool = loop.run_until_complete(bot.db.create_pool())
    bot.loop = loop
    bot.db.pool = pool
    bot.logger = logger
    bot.coc_client = coc.Client(settings['supercell']['user'], settings['supercell']['pass'], key_names=coc_names)

    for extension in initialExtensions:
        try:
            bot.load_extension(extension)
            logger.debug(f"{extension} loaded successfully")
        except Exception as e:
            logger.info(f"Failed to load extension {extension}")
            traceback.print_exc()

    bot.run(token)
