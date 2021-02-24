# utils/image_funcs.py

from functools import lru_cache
from io import BytesIO
from typing import Optional, Tuple

import numpy as np
from numpy.random import randint
from PIL import Image, ImageChops, ImageFilter

FILTERS = {
    "blur": ImageFilter.BLUR,
    "contour": ImageFilter.CONTOUR,
    "detail": ImageFilter.DETAIL,
    "edge": ImageFilter.EDGE_ENHANCE,
    "moreedge": ImageFilter.EDGE_ENHANCE_MORE,
    "emboss": ImageFilter.EMBOSS,
    "find": ImageFilter.FIND_EDGES,
    "sharpen": ImageFilter.SHARPEN,
    "smooth": ImageFilter.SMOOTH,
    "moresmooth": ImageFilter.SMOOTH_MORE,
}


@lru_cache(maxsize=10)
def _shifter(attachment_file: BytesIO, size: Tuple[int, int]) -> BytesIO:

    image_obj = Image.open(attachment_file)

    bands = image_obj.split()

    red_data    = list(bands[0].getdata())
    green_data  = list(bands[1].getdata())
    blue_data   = list(bands[2].getdata())

    for col in [red_data, green_data, blue_data]:
        r_num   = randint(0, len(col))
        low     = randint(1, 15)
        high    = randint(low, 30)
        i[random_num // high : random_num // low] = i[random_num // low : random_num // high]

    new_red = Image.new("L", size)
    new_red.putdata(red_data)

    new_green = Image.new("L", size)
    new_green.putdata(green_data)

    new_blue = Image.new("L", size)
    new_blue.putdata(blue_data)

    new_image = Image.merge("RGB", (new_red, new_green, new_blue))
    new_image = new_image.resize((1024, 1024))

    out_file = BytesIO()
    new_image.save(out_file, format="jpeg")
    out_file.seek(0)
    return out_file

@lru_cache(maxsize=10)
def _jpeg(attachment_file: BytesIO, severity: int) -> BytesIO:
    image_obj = Image.open(attachment_file).convert("RGB")

    out_file = BytesIO()
    image_obj.save(out_file, format="jpeg", quality=severity)
    out_file.seek(0)
    return out_file

def _loop_jpeg(attachment_file: BytesIO, severity: int, loops: int) -> BytesIO:
    for _ in range(loops):
        attachment_file = self._jpeg(attachment_file, severity)
    return attachment_file

@lru_cache(maxsize=10)
def _diff(file_a: BytesIO, file_a_size: Tuple[int, int], file_b: BytesIO, file_b_size: Tuple[int, int]) -> BytesIO:

    new_width = (file_a_size[0] + file_b_size[0]) // 2
    new_height = (file_a_size[1] + file_b_size[1]) // 2

    image_obj_a = Image.open(file_a)
    image_obj_a = image_obj_a.convert("RGB")
    image_obj_a = image_obj_a.resize((new_width, new_height))

    image_obj_b = Image.open(file_b)
    image_obj_b = image_obj_b.convert("RGB")
    image_obj_b = image_obj_b.resize((new_width, new_height))

    new_image = ImageChops.difference(image_obj_a, image_obj_b)

    out_file = BytesIO()
    new_image.save(out_file, format="PNG")
    out_file.seek(0)

    return out_file

@lru_cache(maxsize=10)
async def _get_image(ctx, index: int = 0) -> Tuple[BytesIO, str, Tuple[int, int]]:
    attachment_file = BytesIO()

    if not ctx.message.attachments:
        await ctx.author.avatar_url_as(size=128, format="jpeg").save(
            attachment_file
        )
        filename = ctx.author.display_name + ".png"
        file_size = (128, 128)

    else:
        target = ctx.message.attachments[index]
        await target.save(attachment_file)
        filename = target.filename
        file_size = (target.width, target.height)

    return attachment_file, filename, file_size

@lru_cache(maxsize=10)
def _get_dimension(img_bytes: BytesIO) -> Tuple[BytesIO, int]:
    image_obj = Image.open(img_bytes)
    file_size = image_obj.size
    return img_bytes, file_size

@lru_cache(maxsize=15)
async def _image_ops_func(ctx, img_bytes: Tuple[BytesIO, Optional[BytesIO]]):
    if len(ctx.message.attachments) == 1:
        file_a, _, file_size = await self._get_image(ctx, 0)

    elif img_bytes:
        file_a, file_size = self._get_dimension(img_bytes[0])

    else:
        file_a = BytesIO(
            await ctx.author.avatar_url_as(format="png", size=128).read()
        )
        file_size = (128, 128)

    return file_a, file_size