# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

"""Regression test for issue #3: a resized GIF must keep its transparent
background.

Some GIF files use a palette and mark one palette entry as transparent. After
a resize, the Pillow engine quantizes the RGBA image back to P for GIF output;
the palette still carries the alpha, but Pillow does not set
image.info["transparency"], so the GIF writer drops the transparent index and
the background becomes a solid opaque block.
"""

from io import BytesIO

from PIL import Image, ImageDraw

from thumbor.config import Config
from thumbor.context import Context
from thumbor.engines.pil import Engine

WIDTH = 240
HEIGHT = 160
RED = (255, 0, 0)
TRANSPARENT_INDEX = 255


def make_transparent_gif():
    """A palette GIF whose background is a single transparent index."""
    # everything starts on the transparent index
    image = Image.new("P", (WIDTH, HEIGHT), TRANSPARENT_INDEX)
    palette = [0, 0, 0] * 256
    palette[0:3] = list(RED)
    image.putpalette(palette)

    # a red disc in the middle; everything else keeps the transparent index
    draw = ImageDraw.Draw(image)
    draw.ellipse((WIDTH / 2 - 60, HEIGHT / 2 - 60, WIDTH / 2 + 60, HEIGHT / 2 + 60), fill=0)
    del draw

    buffer = BytesIO()
    # optimize=False keeps the full palette, and with it the transparent index
    image.save(
        buffer, format="GIF", transparency=TRANSPARENT_INDEX, optimize=False
    )
    return buffer.getvalue()


def get_context():
    cfg = Config(
        SECURITY_KEY="ACME-SEC",
        ENGINE="thumbor.engines.pil",
        PILLOW_PRESERVE_INDEXED_MODE=True,
    )
    cfg.LOADER = "thumbor.loaders.file_loader"
    cfg.STORAGE = "thumbor.storages.no_storage"
    return Context(config=cfg)


def count_transparent_pixels(image):
    alpha = image.convert("RGBA").getchannel("A")
    return sum(1 for value in alpha.getdata() if value == 0)


def test_resized_gif_keeps_transparency():
    source_bytes = make_transparent_gif()

    source = Image.open(BytesIO(source_bytes))
    assert source.mode == "P"
    assert count_transparent_pixels(source) > 0

    engine = Engine(get_context())
    engine.extension = ".gif"
    engine.load(source_bytes, ".gif")
    engine.resize(WIDTH // 2, HEIGHT // 2)

    result_bytes = engine.read()

    result = Image.open(BytesIO(result_bytes))
    assert result.format == "GIF"
    assert "transparency" in result.info, (
        "resized GIF lost its transparency index; the background became opaque"
    )
    assert count_transparent_pixels(result) > 0
