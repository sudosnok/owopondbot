# converters.py

import aiohttp
from io import BytesIO
import re

import discord
from discord.ext import commands

from containers import DieEval

class GuildConverter(commands.IDConverter):
    async def convert(self, ctx: commands.Context, arg: str) -> discord.Guild:
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r"<#([0-9]+)>$", argument)
        result = None

        if match is None:
            def check(g):
                return isinstance(g, discord.Guild) and g.name == arg
            
            result = discord.utils.find(check, bot.guilds)
        else:
            guild = bot.get_guild(int(match.group(1)))
        
        if not isinstance(result, discord.Guild):
            raise commands.BadArgument(f"Guild {arg} could not be found.")
        return result

class LinkConverter(commands.Converter):
    png_header = b"\x89\r\n\x1a\n"
    jpg_header = b"\xff\xd8\xff"
    short_read = {'Range': 'bytes=0-10'}

    async def convert(self, ctx: commands.Context, arg: str) -> io.BytesIO:
        bot = ctx.bot
        arg = arg.strip('<>')
        async with bot._session.get(arg, headers=short_read) as res:
            raw_bytes = await res.read()
        if raw_bytes.startswith((self.png_header, self.jpg_header)):
            async with bot._session.get(arg) as real_res:
                img_bytes = BytesIO(await real_res.read())
                return img_bytes
        else:
            raise commands.BadArgument('URL doesn\'t lead to a valid file.')

class CommandConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str) -> commands.Command:
        bot = ctx.bot
        cmd = bot.get_command(arg)
        if cmd:
            return cmd
        raise commands.BadArgument(f'{arg} is not a registered command.')

class DieConverter(commands.Converter):
    die_re = re.compile(r"(\d+)d(\d+)")
    die_mod_re = re.compile(r"(\d+)d(\d+)(\+|\-)(\d+)")

    async def convert(self, ctx: commands.Context, arg: str) -> DieEval:
        arg = arg.lower().replace(' ', '')
        is_die_with_mod = self.die_mod_re.match(arg)
        if is_die_with_mod:
            num, die, op, mod = is_die_with_mod.groups()
            return DieEval(num, die, op, mod)
        is_die = self.die_re.match(arg)
        if is_die:
            num, die = is_die.groups()
            return DieEval(num, die, '+', 0)
        raise commands.BadArgument(f"Argument {argument} is not a valid die format")

class ExceptionConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str) -> commands.CommandError:
        arg = arg.strip().replace(' ', '')
        target = getattr(commands, arg, False)
        if target:
            return target
        else:
            raise commands.BadArgument(f"commands.{arg} is not a valid exception to be handled")