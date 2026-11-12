# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

# Regression test for issue #4: resizing a transparent image (or any
# source) to a very wide, very short size returned an empty picture or a
# 500 error. Every size of at least one pixel per side must return a real
# picture of that size.

import shutil
import tempfile
from io import BytesIO
from os.path import abspath, dirname, join

from PIL import Image
from tornado.testing import gen_test

from tests.base import TestCase
from thumbor.config import Config
from thumbor.context import Context, ServerParameters
from thumbor.importer import Importer


class ExtremeAspectRatioTestCase(TestCase):
    """The three URLs from issue #4, driven through the real pipeline."""

    def setUp(self):
        self.root_path = tempfile.mkdtemp()
        # The issue refers to the course images, not the test fixtures.
        self.loader_path = abspath(
            join(dirname(__file__), "../course/images/")
        )
        self.base_uri = "/image"
        super().setUp()

    def tearDown(self):
        shutil.rmtree(self.root_path)

    def get_context(self):
        cfg = Config(SECURITY_KEY="ACME-SEC")
        cfg.LOADER = "thumbor.loaders.file_loader"
        cfg.FILE_LOADER_ROOT_PATH = self.loader_path
        cfg.STORAGE = "thumbor.storages.file_storage"
        cfg.FILE_STORAGE_ROOT_PATH = self.root_path
        cfg.QUALITY = "keep"

        importer = Importer(cfg)
        importer.import_modules()
        server = ServerParameters(
            8889, "localhost", "thumbor.conf", None, "info", None
        )
        server.security_key = "ACME-SEC"
        return Context(server, cfg, importer)

    @gen_test
    async def test_extreme_aspect_ratio_resizes_return_images(self):
        # /unsafe/800x20/rainbow.png: right size AND visible pixels.
        response = await self.async_fetch("/unsafe/800x20/rainbow.png")
        assert response.code == 200, response.body.decode(
            "utf-8", "replace"
        )
        image = Image.open(BytesIO(response.body))
        assert image.size == (800, 20)
        assert image.convert("RGBA").getchannel("A").getextrema()[1] > 0

        # /unsafe/fit-in/1x1/940x2.png
        response = await self.async_fetch("/unsafe/fit-in/1x1/940x2.png")
        assert response.code == 200, response.body.decode(
            "utf-8", "replace"
        )
        assert Image.open(BytesIO(response.body)).size == (1, 1)

        # /unsafe/fit-in/100x0/940x2.png
        response = await self.async_fetch("/unsafe/fit-in/100x0/940x2.png")
        assert response.code == 200, response.body.decode(
            "utf-8", "replace"
        )
        assert Image.open(BytesIO(response.body)).size == (100, 1)
