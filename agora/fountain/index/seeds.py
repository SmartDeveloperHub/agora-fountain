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

from agora.fountain.index.core import r
import base64


class TypeNotAvailableError(Exception):
    pass


class DuplicateSeedError(Exception):
    pass


class InvalidSeedError(Exception):
    pass


def add_seed(uri, ty):
    from rfc3987 import parse
    parse(uri, rule='URI')
    type_found = False
    type_keys = r.keys('*:types')
    for tk in type_keys:
        if r.sismember(tk, ty):
            type_found = True
            encoded_uri = base64.b64encode(uri)
            if r.sismember('seeds:{}'.format(ty), encoded_uri):
                raise DuplicateSeedError('{} is already registered as a seed of type {}'.format(uri, ty))
            r.sadd('seeds:{}'.format(ty), base64.b64encode(uri))

    if not type_found:
        raise TypeNotAvailableError("{} is not a valid type".format(ty))

    return base64.b64encode('{}|{}'.format(ty, uri))


def get_seed(sid):
    try:
        ty, uri = base64.b64decode(sid).split('|')
        if r.sismember('seeds:{}'.format(ty), base64.b64encode(uri)):
            return {'type': ty, 'uri': uri}
    except TypeError as e:
        raise InvalidSeedError(e.message)

    raise InvalidSeedError(sid)


def delete_seed(sid):
    try:
        ty, uri = base64.b64decode(sid).split('|')
        set_key = 'seeds:{}'.format(ty)
        encoded_uri = base64.b64encode(uri)
        if not r.srem(set_key, encoded_uri):
            raise InvalidSeedError(sid)
    except TypeError as e:
        raise InvalidSeedError(e.message)


def get_seeds():
    def iterator():
        seed_types = r.keys('seeds:*')
        for st in seed_types:
            for seed in list(r.smembers(st)):
                yield base64.b64decode(seed)

    return list(iterator())


def get_type_seeds(ty):
    type_keys = r.keys('*:types')
    type_found = False
    for tk in type_keys:
        if r.sismember(tk, ty):
            type_found = True
            break

    if not type_found:
        raise TypeNotAvailableError(ty)

    return [base64.b64decode(seed) for seed in list(r.smembers('seeds:{}'.format(ty)))]
