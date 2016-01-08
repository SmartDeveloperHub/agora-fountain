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

import logging
import os

__author__ = 'Fernando Serena'


def _api_port():
    return int(os.environ.get('FOUNTAIN_API_PORT', 5002))


def _redis_conf(def_host, def_db, def_port):
    return {'host': os.environ.get('FOUNTAIN_DB_HOST', def_host),
            'db': os.environ.get('FOUNTAIN_DB_DB', def_db),
            'port': os.environ.get('FOUNTAIN_DB_PORT', def_port)}


class Config(object):
    STORE_PATHS = {
        'graph': 'graph_store'
    }
    PORT = _api_port()


class DevelopmentConfig(Config):
    DEBUG = True
    LOG = logging.DEBUG
    REDIS = _redis_conf('localhost', 1, 6379)
    STORE = 'persist'


class TestingConfig(Config):
    DEBUG = False
    LOG = logging.DEBUG
    REDIS = _redis_conf('localhost', 2, 6379)
    TESTING = True
    STORE = 'memory'


class ProductionConfig(Config):
    DEBUG = False
    LOG = logging.INFO
    REDIS = _redis_conf('redis', 1, 6379)
    STORE = 'persist'
