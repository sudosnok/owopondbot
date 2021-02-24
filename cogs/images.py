# cogs/images.py

from functools import lru_cache
from io import BytesIO, StringIO
import time
from typing import Optional, Tuple, Union

from discord.ext import commands
from matplotlib import pyplot as plt
import numpy as np
from PIL import Image, ImageChops, ImageFilter, ImageOps

from utils.converters import LinkConverter
from utils import image_funcs


class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def embed_bytes(
        self,
        ctx: commands.Context,
        message: str,
        fileout: Union[BytesIO, StringIO],
        filename: str,
        timediff: float,
    ):
        f = discord.File(fileout, filename)
        e = discord.Embed(title=message, colour=discord.Colour.random())
        e.set_image(url=f'attachment://{filename}')
        await ctx.send(embed=e, file=f)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait=False)
    async def shift(self, ctx: commands.Context, *image_bytes: Optional[LinkConverter]):
        """Shifts the RGB bands of the attachment, link or author's profile picture"""
        fileout, filesize = await image_funcs._image_ops_func(ctx, image_bytes)

        start       = time.time()
        new_file    = image_funcs._shifter(fileout, filesize)
        end         = time.time()

        await self.embed_bytes(ctx, 'Shifting done', fileout, 'shifted.png', end-start)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait=False)
    async def morejpeg(
        self,
        ctx: commands.Context,
        severity: int = 15,
        *image_bytes: Optional[LinkConverter]
    ):
        """Adds jpeg compression proportional to the severity arg to the attachment, link or author's profile picture"""

        if not (0 <= severity <= 100):
            raise commands.BadArgument("Severity argument must be between 0 and 100 inclusive")
        severity = 101 - severity

        fileout = image_bytes or (await image_funcs.get_image(ctx, 0))[0]

        start = time.time()
        fileout = await self.bot.loop.run_in_executor(
            None, image_funcs._loop_jpeg, fileout, severity, 1
        )
        end = time.time()

        await self.embed_bytes(ctx, "Jpegifying done", fileout, 'diff.jpg', end-start)


    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait=False)
    async def diff(
        self,
        ctx: commands.Context,
        *image_bytes: Optional[LinkConverter]
    ):
        """Returns the difference of two images, both must be as links or both as attachments"""
        if len(ctx.message.attachments) == 2:
            file_a, _, file_a_size = await image_funcs._get_image(ctx, 0)
            file_b, _, file_b_size = await image_funcs._get_image(ctx, 1)
        elif len(image_bytes) == 2:
            file_a, file_a_size = image_funcs._get_dimension(image_bytes[0])
            file_b, file_b_size = image_funcs._get_dimension(image_bytes[1])
        else:
            raise commands.BadArgument("Images must both be attachments or links, not a mixture")

        start   = time.time()
        fileout = image_funcs._diff(file_a, file_a_size, file_b, file_b_size)
        end     = time.time()

        await self.embed_bytes(ctx, "Difference gotten", fileout, 'diff.png', end-start)

    @commands.command(name="invert", aliases=["negative"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait=False)
    async def _invert(self, ctx: commands.Context, *img_bytes: Optional[LinkConverter]):
        """Inverts a uploaded image, link or the authors profile picture to negative"""

        file_a, file_size = await image_funcs._image_ops_func(ctx, img_bytes)

        start = time.time()

        image_obj = Image.open(file_a)
        try:
            image_obj = ImageOps.invert(image_obj)
        except:
            image_obj = image_obj.convert(mode="RGB")
            image_obj = ImageOps.invert(image_obj)
        new_file = BytesIO()
        image_obj.save(new_file, format="PNG")
        new_file.seek(0)

        end = time.time()

        await self.embed_file(ctx, "Inverting finished", new_file, "inverted.png", end - start)

    @commands.command(name="poster")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait=False)
    async def _poster(
        self, ctx: commands.Context, bits: int = 8, *img_bytes: Optional[LinkConverter]
    ):
        """Changes the number of bits (1 - 8 inc) dedicated to each colour channel, image must be an attachment, a link or the authors profile picture"""

        if not (1 <= bits <= 8):
            raise commands.BadArgument(
                "Bits argument should be between 1 and 8 inclusive"
            )

        file_a, file_size = await image_funcs._image_ops_func(ctx, img_bytes)

        start = time.time()

        image_obj = Image.open(file_a)
        try:
            image_obj = ImageOps.posterize(image_obj, bits)
        except:
            image_obj = image_obj.convert(mode="RGB")
            image_obj = ImageOps.posterize(image_obj, bits)
        new_file = BytesIO()
        image_obj.save(new_file, format="PNG")
        new_file.seek(0)

        end = time.time()

        await self.embed_file(ctx, "Postering done", new_file, "poster.png", end - start)

    @commands.command(name="filter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait=False)
    async def _filter(
        self, ctx: commands.Context, filter_type: str, *img_bytes: Optional[LinkConverter]
    ):
        """Applies a filter to an uploaded image, link or the authors profile picture"""

        filter_type = filter_type.lower()

        if not (filter_type in image_funcs.FILTERS):
            raise commands.BadArgument(
                "Filter must be one of those in ImageFilter docs"
            )

        file_a, file_size = await image_funcs._image_ops_func(ctx, img_bytes)

        start = time.time()

        image_obj = Image.open(file_a)
        try:
            image_obj = image_obj.filter(image_funcs.FILTERS[filter_type])
        except:
            image_obj = image_obj.convert(mode="RGB")
            image_obj = image_obj.filter(image_funcs.FILTERS[filter_type])
        new_file = BytesIO()
        image_obj.save(new_file, format="png")
        new_file.seek(0)

        end = time.time()

        await self.embed_file(ctx, "Applying the filter done", new_file, "filtered.png", end - start)

    @commands.command(name="rotate")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait=False)
    async def _rotate(
        self, ctx: commands.Context, degrees: int, *img_bytes: Optional[LinkConverter]
    ):
        """Rotates an attached image, link or the authors profile picture some degrees, 360 returns it to original position"""
        degrees = degrees % 360 if degrees > 360 else degrees

        file_a, file_size = await image_funcs._image_ops_func(ctx, img_bytes)

        start = time.time()

        image_obj = Image.open(file_a)
        image_obj = image_obj.rotate(angle=degrees)
        fileout = BytesIO()
        image_obj.save(fileout, format="PNG")
        fileout.seek(0)
        end = time.time()

        await self.embed_file(ctx, "Rotationings finished", fileout, "rotated.png", end-start)

def setup(bot):
    bot.add_cog(Images(bot))