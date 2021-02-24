# cogs/events.py

from functools import lru_cache
import traceback

from discord.ext import commands

from utils.converters import ExceptionConverter


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._ignored = bot._ignored or {commands.CommandNotFound,}

    @lru_cache(maxsize=3)
    def traceback_formatter(self, exc: Exception) -> str:
        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
        if self.bot._print_exc:
            print(tb)
        return '\n'.join(tb[-2:])

    @commands.group(invoke_without_command=True)
    async def ignored(self, ctx: commands.Context):
        return await ctx.send(', '.join(map(str, self._ignored)))

    @ignored.command()
    @commands.is_owner()
    async def add(self, ctx: commands.Context, target: ExceptionConverter):
        if target not in self._ignored:
            self._ignored.append(target)
            return
        return await ctx.send(f'{target} seems to already be ignored.')

    @ignored.command()
    @commands.is_owner()
    async def remove(self, ctx: commands.Context, target: ExceptionConverter):
        if target not in self._ignored:
            return await ctx.send(f'{target} wasn\'t in the list to ignore.')
        self._ignored.remove(target)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, exc: commands.CommandError):
        if hasattr(ctx.command, 'on_error'): return

        if isinstance(exc, self._ignored): return

        exc = getattr(exc, 'original', exc)

        if isinstance(exc, commands.CommandOnCooldown):
            if ctx.author.id == bot.owner_id:
                return await ctx.reinvoke()

        exc_info = self.traceback_formatter(exc)
        return await ctx.send(exc_info)
        
def setup(bot):
    bot.add_cog(Events(bot))