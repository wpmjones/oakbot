import traceback
import git
import os
from loguru import logger
from discord.ext import commands
from config import settings

logger.add("oakbot.log", rotation="100MB",
           format="{time:YYYY-MM-DD HH:mm:ss} {level} {message}", level="INFO")
logger.info("Starting bot")

description = """Welcome to The Arborist - by TubaKid

All commands must begin with a slash"""

bot = commands.Bot(command_prefix="/", description=description, case_insensitive=True)
bot.remove_command("help")
bot.repo = git.Repo(os.getcwd())


@bot.event
async def on_ready():
    logger.info("-------")
    logger.info(f"Logged in as {bot.user}")
    logger.info("-------")
    channel = bot.get_channel(settings['oakChannels']['testChat'])
    await channel.send("The Arborist is now planting trees")


initialExtensions = ["cogs.general", "cogs.members", "cogs.elder", "cogs.owner"]

if __name__ == "__main__":
    for extension in initialExtensions:
        try:
            bot.load_extension(extension)
            logger.debug(f"{extension} loaded successfully")
        except Exception as e:
            logger.info(f"Failed to load extension {extension}")
            traceback.print_exc()

bot.run(settings['discord']['oakbotToken'])
