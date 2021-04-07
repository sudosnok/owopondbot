# cogs/pins.py

from datetime import datetime

import discord
from discord.ext import commands
import typing


class Pins(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pond_server = 227088162390802433
        self.gen_channel = 227088162390802433  # same because default channel
        self.pin_channel = 707925869162659960

    def generate_embed(self, msg: discord.Message) -> discord.Embed:
        e = discord.Embed(colour=discord.Colour.random())
        e.set_author(name=msg.author.display_name, icon_url=msg.author.avatar_url)
        e.description = msg.content + f"\n[Click to jump]({msg.jump_url} \"Jump to message\")"
        e.set_footer(text=datetime.utcnow().strftime(r"%d %b '%y; %I:%M %p"))
        return e

    @commands.command(name='pins')
    @commands.is_owner()
    async def update_pins(self, ctx, target_after=None):
        """Pulls pinned messages to the pinned messages channel to reduce overflow"""
        general = self.bot.get_channel(self.gen_channel)
        pins = self.bot.get_channel(self.pin_channel)

        if target_after:
            try:
                after = datetime.strptime(target_after, r"%d:%m:%y")
            except ValueError:
                raise commands.BadArgument(
                    'Time passed did not match "%d:%m:%y" format.'
                )
            else:
                after = datetime.strptime("16 9 18", r"%y %m %d")  # general creation date

        messages = await general.pins()
        messages: typing.List[discord.Message] = messages[::-1]  # go from oldest to newest
        messages = [m for m in messages if m.created_at >= after]  # filter out messages by creation date
        embeds = []

        for message in messages:
            embed = self.generate_embed(message)
            print(f'Made embed number : {len(embeds)}')
            embeds.append(embed)
            try:
                await pins.send(embed=embed)
            except Exception as e:
                raise e

    @commands.command()
    async def pin(self, ctx, msg: typing.Optional[discord.Message]):
        """Pin a message by providing a link, will be posted in #pins"""
        pins = self.bot.get_channel(self.pin_channel)

        try:
            message = msg or ctx.message.reference.resolved
        except AttributeError:
            raise commands.BadArgument('Could not resolve message reference')
        else:
            message = msg

        embed = self.generate_embed(message)
        await pins.send(embed=embed)


def setup(bot):
    bot.add_cog(Pins(bot))