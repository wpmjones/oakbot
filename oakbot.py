import traceback
import sys
import coc
import asyncio
import aiohttp
import discord

from discord.ext import commands
from coc.ext import discordlinks
from cogs.utils import context
from cogs.utils.db import Psql
from datetime import datetime
from loguru import logger
from config import settings

enviro = "LIVE"

initial_extensions = ["cogs.general",
                      "cogs.elder",
                      "cogs.owner",
                      "cogs.admin",
                      "cogs.war"
                      ]

if enviro == "LIVE":
    token = settings['discord']['oakbot_token']
    prefix = "/"
    log_level = "INFO"
    coc_names = "galaxy"
    initial_extensions.append("cogs.members")
    initial_extensions.append("cogs.war_state")
    initial_extensions.append("cogs.throle")
    initial_extensions.append("cogs.background")
    initial_extensions.append("cogs.cwl")
    coc_email = settings['supercell']['user']
    coc_pass = settings['supercell']['pass']
elif enviro == "home":
    token = settings['discord']['test_token']
    prefix = ">"
    log_level = "DEBUG"
    coc_names = "ubuntu"
    coc_email = settings['supercell']['user2']
    coc_pass = settings['supercell']['pass2']
else:
    token = settings['discord']['test_token']
    prefix = ">"
    log_level = "DEBUG"
    coc_names = "dev"
    coc_email = settings['supercell']['user2']
    coc_pass = settings['supercell']['pass2']

description = """Welcome to The Arborist - by TubaKid

All commands must begin with a slash"""

coc_client = coc.login(coc_email,
                       coc_pass,
                       client=coc.EventsClient,
                       key_names=coc_names,
                       key_count=2,
                       correct_tags=True)

links_client = discordlinks.login(settings['links']['user'],
                                  settings['links']['pass'])


class OakBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=prefix,
                         description=description,
                         case_insensitive=True)
        self.remove_command("help")
        coc_client.bot = self
        self.coc = coc_client
        self.links = links_client
        self.color = discord.Color.green()
        self.logger = logger
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.loop.create_task(self.after_ready())

        for extension in initial_extensions:
            try:
                self.load_extension(extension)
                self.logger.debug(f"{extension} loaded successfully")
            except Exception as extension:
                self.logger.error(f"Failed to load extension {extension}.", file=sys.stderr)
                traceback.print_exc()

    @property
    def log_channel(self):
        return self.get_channel(settings['log_channels']['oak'])

    async def send_message(self, message):
        if len(message) < 2000:
            await self.log_channel.send(f"`{message}`")
        else:
            await self.log_channel.send(f"`{message[:1950]}`")

    def send_log(self, message):
        asyncio.ensure_future(self.send_message(message))

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=context.Context)
        if ctx.command is None:
            return
        async with ctx.acquire():
            await self.invoke(ctx)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send("This command cannot be used in private messages.")
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send("Oops. This command is disabled and cannot be used.")
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                self.logger.error(f"In {ctx.command.qualified_name}:", file=sys.stderr)
                traceback.print_tb(original.__traceback__)
                self.logger.error(f"{original.__class__.__name__}: {original}", file=sys.stderr)
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(error)

    async def on_error(self, event_method, *args, **kwargs):
        e = discord.Embed(title="Discord Event Error", color=0xa32952)
        e.add_field(name="Event", value=event_method)
        e.description = f"```py\n{traceback.format_exc()}\n```"
        e.timestamp = datetime.utcnow()

        args_str = ["```py"]
        for index, arg in enumerate(args):
            args_str.append(f"[{index}]: {arg!r}")
        args_str.append("```")
        e.add_field(name="Args", value="\n".join(args_str), inline=False)
        try:
            await self.log_channel.send(embed=e)
        except:
            pass

    async def on_ready(self):
        activity = discord.Game(" with fertilizer")
        await bot.change_presence(activity=activity)
        self.coc.add_clan_updates("#CVCJR89")
        clan = await self.coc.get_clan("#CVCJR89")
        self.coc.add_player_updates(*[m.tag for m in clan.members])

    async def after_ready(self):
        await self.wait_until_ready()
        logger.add(self.send_log, level=log_level)

    async def close(self):
        await super().close()
        await self.coc.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        pool = loop.run_until_complete(Psql.create_pool())
        bot = OakBot()
        bot.pool = pool
        bot.loop = loop
        bot.run(token, reconnect=True)
    except:
        traceback.print_exc()
