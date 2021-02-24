# main.py

# main.py

import asyncio
import aiohttp

import discord
from discord.ext import commands

import config

exts = [
    'jishaku',
    'cogs.events',
    'cogs.images',
    'cogs.osrs',
]

class MyContext(commands.Context):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def invoked_parents(self):
        view = self.view
        idx, prev = view.index, view.previous
        view.index = 0+len(self.prefix)
        view.previous = 0+len(self.prefix)
        #view.skip_ws()
        invoked_parents = {}
        print('we here')
        for parent in self.command.parents:
            print('iterating')
            invoked_parents[parent] = view.get_word()
            view.skip_ws()
        self.view.index = idx
        self.view.previous = prev
        return invoked_parents


class Bot(commands.Bot):
    _ignored = (commands.CommandNotFound,)
    headers = {'user-agent': f'DiscordBot; Python/3.8.3 aiohttp/{aiohttp.__version__}'}
    smol_bytes = {'Range': 'bytes=0-10'}
    def __init__(self, command_prefix, **kwargs):
        super().__init__(command_prefix, **kwargs)
    
    async def connect(self, *, reconnect=True):
        self._session = aiohttp.ClientSession(headers=self.headers)

        for ext in exts:
            try:
                self.load_extension(ext)
                print(ext, ' loaded')
            except Exception as exc:
                raise exc
        return await super().connect(reconnect=reconnect)
    
    async def get_context(self, message, cls=MyContext):
        return await super().get_context(message, cls=MyContext)

    async def on_ready(self):
        print('Ready!')

    async def close(self):
        await self._session.close()
        return await super().close()
    
if __name__ == '__main__':
    allowed_mentions = discord.AllowedMentions(everyone=False, users=True, roles=False)
    intents = discord.Intents.all()
    owner_id = 273035520840564736
    bot = Bot('.', allowed_mentions=allowed_mentions, intents=intents, owner_id=owner_id)
    print('Created bot object')
    bot.run(config.TOKEN)
    print('Bot object was killed')
