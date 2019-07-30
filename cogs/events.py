from discord.ext import commands


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.coc.add_events(
            self.on_clan_member_donation,
            self.on_clan_member_received
        )
        self.bot.coc._clan_retry_interval = 60
        self.bot.coc.start_updates('clan')

        self.channel_config_cache = {}

    async def cog_command_error(self, ctx, error):
        await ctx.send(str(error))

    def cog_unload(self):
        self.bulk_report.cancel()
        self.batch_insert_loop.cancel()
        self.check_for_timers_task.cancel()
        try:
            self.bot.coc.extra_events['on_clan_member_donation'].remove(
                self.on_clan_member_donation)
            self.bot.coc.extra_events['on_clan_member_received'].remove(
                self.on_clan_member_received)
        except ValueError:
            pass

    @tasks.loop(minutes=5)
    async def 