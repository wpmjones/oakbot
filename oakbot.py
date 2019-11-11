import traceback
import git
import os
import coc
import asyncio
import discord

from discord.ext import commands
from oakdb import OakDB
from loguru import logger
from config import settings

enviro = "LIVE"

if enviro == "LIVE":
    token = settings['discord']['oakbotToken']
    prefix = "/"
    log_level = "INFO"
    coc_names = "vps"
elif enviro == "work":
    token = settings['discord']['testToken']
    prefix = ">"
    log_level = "DEBUG"
    coc_names = "work"
else:
    token = settings['discord']['testToken']
    prefix = ">"
    log_level = "DEBUG"
    coc_names = "dev"

description = """Welcome to The Arborist - by TubaKid

All commands must begin with a slash"""

bot = commands.Bot(command_prefix=prefix, description=description, case_insensitive=True)


@bot.event
async def on_ready():
    logger.info("-------")
    logger.info(f"Logged in as {bot.user}")
    logger.info("-------")
    bot.test_channel = bot.get_channel(settings['oakChannels']['testChat'])
    logger.info("The Arborist is now planting trees")
    activity = discord.Game(" with fertilizer")
    await bot.change_presence(activity=activity)
    await bot.test_channel.send("The Arborist is now planting trees")


def send_log(message):
    asyncio.ensure_future(send_message(message))


async def send_message(message):
    if len(message) < 2000:
        await bot.get_channel(settings['logChannels']['oak']).send(f"`{message}`")
    else:
        await bot.get_channel(settings['logChannels']['oak']).send(f"`{message[:1950]}`")


async def after_ready():
    await bot.wait_until_ready()
    logger.add(send_log, level=log_level)

initialExtensions = ["cogs.general",
                     "cogs.members",
                     "cogs.elder",
                     "cogs.owner",
                     "cogs.admin",
                     "cogs.warrole",
                     ]

if __name__ == "__main__":
    bot.remove_command("help")
    bot.repo = git.Repo(os.getcwd())
    bot.db = OakDB(bot)
    loop = asyncio.get_event_loop()
    pool = loop.run_until_complete(bot.db.create_pool())
    loop.create_task(after_ready())
    bot.loop = loop
    bot.db.pool = pool
    bot.logger = logger
    bot.coc_client = coc.login(settings['supercell']['user'],
                               settings['supercell']['pass'],
                               client=coc.EventsClient,
                               key_names=coc_names,
                               correct_tags=True)

    for extension in initialExtensions:
        try:
            bot.load_extension(extension)
            logger.debug(f"{extension} loaded successfully")
        except Exception as e:
            logger.info(f"Failed to load extension {extension}")
            traceback.print_exc()

    bot.run(token)