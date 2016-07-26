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
from base64 import b64encode
from functools import wraps

__author__ = 'Fernando Serena'


class Cache(dict):
    def __init__(self, **kwargs):
        super(Cache, self).__init__(**kwargs)
        self.__observers = []

    def watch(self, other):
        if isinstance(other, Cache):
            if self not in other.__observers:
                other.__observers.append(self)

    def clear(self):
        super(Cache, self).clear()
        for obs in self.__observers:
            obs.clear()


def cached(cache):
    """

    :param cache:
    :return:
    """
    def d(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            if not isinstance(cache, Cache):
                raise AttributeError('Cache type is not valid')
            cache_key = b64encode(f.__name__ + str(args[0:]) + str(kwargs))
            if cache_key not in cache:
                result = f(*args, **kwargs)
                cache[cache_key] = result

            return cache[cache_key]

        return wrap
    return d


def notify(cache):
    """

    :param cache:
    :return:
    """
    def d(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            result = f(*args, **kwargs)
            cache.clear()
            return result
        return wrap
    return d
