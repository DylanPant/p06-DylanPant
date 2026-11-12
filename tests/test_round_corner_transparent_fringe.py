# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from PIL import Image
from tornado.testing import gen_test

from tests.base import FilterTestCase


class RoundCornerTransparentFringeTestCase(FilterTestCase):
    @gen_test
    async def test_transparent_corner_keeps_colors_and_uses_alpha(self):
        # With the transparent flag set, the pixels on the curve must keep
        # their original color and become partly transparent, so the corner
        # fades into the background with no dark ring. Today those pixels are
        # left fully opaque and their colors are scaled toward black.
        radius = 60
        image = await self.get_filtered(
            "source.jpg",
            "thumbor.filters.round_corner",
            f"round_corner({radius},255,255,255,1)",
            mode="RGBA",
        )

        source = Image.open(self.get_fixture_path("source.jpg")).convert(
            "RGB"
        )
        width, height = image.size
        pixels = image.load()
        source_pixels = source.load()

        # The four corner squares of the requested radius.
        corners = [
            (0, 0),
            (width - radius, 0),
            (0, height - radius),
            (width - radius, height - radius),
        ]

        for corner_x, corner_y in corners:
            partially_transparent = []
            for y in range(corner_y, corner_y + radius):
                for x in range(corner_x, corner_x + radius):
                    if 0 < pixels[x, y][3] < 255:
                        partially_transparent.append((x, y))

            assert partially_transparent, (
                "no partially transparent pixel was found in the corner at "
                f"({corner_x}, {corner_y}); the edge is not smoothed through "
                "the alpha channel"
            )

            for x, y in partially_transparent:
                red, green, blue, _alpha = pixels[x, y]
                source_red, source_green, source_blue = source_pixels[x, y]
                assert abs(red - source_red) <= 8, (
                    f"pixel ({x}, {y}) on the rounded corner has red {red} "
                    f"but the source has {source_red}; the curve should keep "
                    "its original color and fade through alpha instead"
                )
                assert abs(green - source_green) <= 8, (
                    f"pixel ({x}, {y}) on the rounded corner has green "
                    f"{green} but the source has {source_green}; the curve "
                    "should keep its original color and fade through alpha "
                    "instead"
                )
                assert abs(blue - source_blue) <= 8, (
                    f"pixel ({x}, {y}) on the rounded corner has blue {blue} "
                    f"but the source has {source_blue}; the curve should keep "
                    "its original color and fade through alpha instead"
                )
