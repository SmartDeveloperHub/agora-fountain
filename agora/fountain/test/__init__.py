"""
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  This file is part of the Smart Developer Hub Project:
    http://www.smartdeveloperhub.org

  Center for Open Middleware
        http://www.centeropenmiddleware.com/
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Copyright (C) 2015 Center for Open Middleware.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

            http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
"""

__author__ = 'Fernando Serena'

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
