# cogs/osrs.py

from datetime import datetime
from io import BytesIO
from itertools import repeat
from json.decoder import JSONDecodeError
from typing import Dict, List, Tuple, Union

from bs4 import BeautifulSoup
import discord
from discord.ext import commands
from matplotlib import pyplot as plt
import matplotlib as mpl
from numpy.random import randint

from config import USERAGENT
from utils.containers import OSRSObject

WIKI_BASE = 'https://oldschool.runescape.wiki/w/{item}'
DETAIL = 'https://services.runescape.com/m=itemdb_oldschool/api/catalogue/detail.json?item={item_id}'
GRAPH = 'https://services.runescape.com/m=itemdb_oldschool/api/graph/{item.id}.json'
TITLE = "{item.name}: avg={sum(prices)//len(dates):,}gp, \nmax={max(prices):,}gp, min={min(prices):,}gp"

class Oldschool(commands.Cog):
    items: Dict[str, OSRSObject] = {}
    max_width = 3

    def __init__(self, bot):
        self.bot = bot
        self._session = bot._session
        self.plt = plt
        self.plt_dim = (1, 1)
        self.plt.subplots(*self.plt_dim)

    @property
    def print(self):
        return '\n'.join(self.items.keys())

    async def get_item(self, item_name: str) -> int:
        item = item_name.replace(' ',  '_')
        page = await self._session.get(WIKI_BASE.format(item), headers=USERAGENT)
        page = await page.text()
        soup = BeautifulSoup(page, features='html.parser')
        return int(soup.find('div', {'class': 'GEdataprices'})['data-itemid'])
    
    async def make_object(self, item_id: Union[int, str]) -> OSRSObject:
        if isinstance(item_id, str):
            item_id = await self.get_item(item_id)
            await self.get_price_data(item_id)

        elif isinstance(item_id, int):
            data = await self._session.get(DETAIL.format(item_id), headers=USERAGENT)
            data = await data.json()
            return OSRSObject(data)

        else:
            return None
    
    async def get_price_data(self, item: OSRSObject) -> dict:
        data = await self._session.get(GRAPH.format(item.id), headers=USERAGENT)
        return await data.json()


    async def make_graph(self, item: OSRSObject, graph: mpl.axes.SubplotBase):
        data = await self.get_price_data(item)
        dates, prices = [], []
        for k, v in data['daily'].items():
            dates.append(datetime.fromtimestamp(int(k//1000)))
            prices.append(int(v))
        graph.plot(dates, prices)
        graph.xlabel('Date')
        graph.ylabel('Prices')
        graph.title(TITLE.format(item, dates=dates, prices=prices), pad=8.0)
        return graph


    def get_subplots(self, num_items: int):
        if num_items > self.max_width:
            rows, remainder = divmod(num_items, self.max_width)
            if remainder != 0:
                rows += 1
            cols = self.max_width
            start_idx = int(str(rows) + str(cols) + '1')
            end_idx = start_idx + (num_items)
            out = [plt.subplot(num) for num in range(start_idx, end_idx)]
        else:
            start_idx = 111
            end_idx = start + num_items
            out = [plt.subplot(num) for num in range(start_idx, end_idx)]
        return out

    
    @commands.group(invoke_without_command=True, name='graph')
    @commands.max_concurrency(1, commands.BucketType.user, wait=False)
    async def _graph(self, ctx: commands.Context, *item_name: Tuple[str]):
        """Attempts to draw a graph of the price of an item over the last 180 days"""
        item_name = '_'.join(item_name)
        item = await self.make_object(item_name)
        data = (await self.get_price_data(item))['daily']
        dates, prices = [], []
        for k, v in data.items():
            dates.append(datetime.fromtimestamp(int(k//1000)))
            prices.append(int(v))
        plt.plot(dates, prices)
        plt.xlabel('Date')
        plt.ylabel('Prices')
        now = datetime.utcnow().strftime("(%d-%m)")
        plt.title(TITLE.format(item, dates=dates, prices=prices), pad=8.0)

        plot_bytes = BytesIO()
        plt.savefig(plot_bytes, format='png')
        plot_bytes.seek(0)
        plt.clf() # clears the self.plt figure for the next cmd

        fileout = discord.File(plot_bytes, filename=item.name)
        embed = discord.Embed(title=item.name, colour=discord.Colour.random())
        embed.set_image(url=f"attachment://{item.name}")

        await ctx.send(embed=embed, file=fileout)
        
    @_graph.command()
    async def add(self, ctx: commands.Context, *item_name: Tuple[str]):
        """Adds an item to an existing plot """
        if len(self.items.keys()) == 9:
            return await ctx.send("You can't have more than 9 items per plot, here are the items in the list if you want to remove one;\n" + self.print)
        item = await self.make_object(item_name)
        if not self.items.get(item.name, False):
            self.items[item.name] = item
            return await ctx.send(f'{item.name} added to the plots')
        return await ctx.send('Item is already in the list to show')

    @_graph.command()
    async def remove(self, ctx: commands.Context, *item_name: Tuple[str]):
        """Removes the given item name from the graphs to be plotted"""
        item = self.make_object(item_name)
        if self.items.get(item.name, False):
            del self.items[item.name]
            return await ctx.send(f"{item.name} removed from the plots")
        return await ctx.send(f"{item.name} wasn't in the list of items to plot")

    @_graph.command(name='list')
    async def _list(self, ctx: commands.Context):
        """Shows all items currently stored waiting for graphing"""
        return await ctx.send(self.print)

    @_graph.command()
    async def show(self, ctx: commands.Context, seperate: bool = True):
        """Constructs the actual plots"""
        number_of_items = len(list(self.items.keys()))
        async with ctx.typing():
            if seperate:
                axes = self.get_subplots(number_of_items)
                newplots = [self.make_graph(item, axes) for item, axes in zip(list(self.items.values()), axes)]
                
                graph_bytes = BytesIO()
                plt.savefig(graph_bytes, format='png')
                graph_bytes.seek(0)

                _ = [plot.clear() for plot in newplots] # just a tidy up after making the graphs
                
                f = discord.File(graph_bytes, filename='OSRS-items.png')
                e = discord.Embed(title="Your graphs ;", colour=discord.Color.random())
                e.set_image(url='attachment://OSRS-items.png')

                return await ctx.send(embed=e, file=f)
            else:
                newplots = [self.make_graph(item, axes) for item, axes in zip(list(self.items.values()), repeat(plt.subplot(111)))]

                graph_bytes = BytesIO()
                plt.savefig(graph_bytes, format='png')
                graph_bytes.seek(0)

                _ = [plot.clear() for plot in newplots]

                f = discord.File(graph_bytes, filename='OSRS-items.png')
                e = discord.Embed(title="Your graphs ;", colour=discord.Color.random())
                e.set_image(url='attachment://OSRS-items.png')

                return await ctx.send(embed=e, file=f)

    @commands.command(aliases=['mw'])
    async def max_width(self, ctx: commands.Context, new_maxwidth: int):
        """Sets a new max_width for graphs, between 2 and 4 inclusive"""
        if 2 <= new_maxwidth <= 4:
            prev = self.max_width
            self.max_width = new_maxwidth
            return await ctx.send(f"max_width changed; {prev} -> {self.max_width}")
        else:
            raise commands.BadArgument('The new max width must be between 2 and 4 inclusive')

    @commands.command(name='randitem')
    async def randomitem(self, ctx: commands.Context):
        """Attempts to get a random item from the oldschool database"""
        item_id = randint(0, 25514)
        item = None
        while not item:
            try:
                item = await self.make_object(item_id)
            except (KeyError, JSONDecodeError):
                pass # just means the id wasnt a real item (a duplicate or untradeable)
        if item:
            return await ctx.send(item.print)


def setup(bot):
    bot.add_cog(Oldschool(bot))

