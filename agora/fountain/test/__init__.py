__author__ = 'fernando'

import unittest
from agora.fountain.server import app
from nose.tools import *


def setup():
    from agora.fountain.server.config import TestingConfig

    app.config['TESTING'] = True
    app.config.from_object(TestingConfig)
    app.config['STORE'] = 'memory'

    from agora.fountain.index.core import r
    r.flushdb()

    from agora.fountain import api


class FountainTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def tearDown(self):
        pass

    def get(self, path, exp_code=200, message=None):
        rv = self.app.get(path)
        if message is None:
            message = 'There is a problem with the request'
        eq_(rv.status_code, exp_code, message)
        return rv.data

    def post(self, path, data, content_type='text/turtle', exp_code=201, message=None):
        rv = self.app.post(path, data=data, headers={'Content-Type': content_type})
        if message is None:
            message = 'The resource was not created properly'
        eq_(rv.status_code, exp_code, message)
        return rv.data

    def delete(self, path, error_message=None):
        rv = self.app.delete(path)
        if error_message is None:
            error_message = "The resource couldn't be deleted"
        eq_(rv.status_code, 200, error_message)
        return rv.data


def teardown():
    pass
