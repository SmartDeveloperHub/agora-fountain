__author__ = 'fernando'

import unittest
from agora.fountain.server import app


def setup():
    from agora.fountain.server.config import TestingConfig

    app.config['TESTING'] = True
    app.config.from_object(TestingConfig)

    from agora.fountain.index.core import r
    r.flushdb()

    from agora.fountain import api


class FountainTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def tearDown(self):
        pass


def teardown():
    pass
