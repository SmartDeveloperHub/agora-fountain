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
    """
    Special dictionary to be used as a cache that offers mechanisms to watch and clear (on cascade)
    """
    def __init__(self, **kwargs):
        super(Cache, self).__init__(**kwargs)
        self.__watchers = []
        self.stable = 1

    def watch(self, other):
        # type: (Cache) -> None
        """
        :param other: Cache object to watch
        """
        if isinstance(other, Cache):
            if self not in other.__watchers:
                other.__watchers.append(self)

    def clear(self):
        # type: () -> None
        """
        Clear all data and send the message to all watchers
        """
        super(Cache, self).clear()
        for obs in self.__watchers:
            obs.clear()


def cached(cache, level=0):
    # type: (Cache, int) -> Callable
    """

    :rtype: Callable
    :param cache: The cache object to be used
    :param level: Level at which cached data should be considered stable
    """
    def d(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            if not isinstance(cache, Cache):
                raise AttributeError('Cache type is not valid')
            cache_key = b64encode(f.__name__ + str(args[0:]) + str(kwargs))
            if not cache.stable >= level or cache_key not in cache:
                result = f(*args, **kwargs)
                cache[cache_key] = result
            return cache[cache_key]
        return wrap
    return d

