__author__ = 'fernando'

import unittest
from agora.fountain.api import app
from agora.fountain.index.core import r
from agora.fountain.vocab.schema import graph
from agora.fountain.server.config import TestingConfig


def setup():
    app.config['TESTING'] = True
    app.config.from_object(TestingConfig)
    for c in graph.contexts():
        graph.remove_context(c)
    r.flushdb()


class FountainTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def tearDown(self):
        pass


def teardown():
    pass
