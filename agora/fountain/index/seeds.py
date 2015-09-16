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

import base64

from agora.fountain.index.core import r
from agora.fountain.index import core as index
from agora.fountain.exceptions import FountainError


class TypeNotAvailableError(FountainError):
    pass


class DuplicateSeedError(FountainError):
    pass


class InvalidSeedError(FountainError):
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
            break

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


def delete_type_seeds(ty):
    r.delete('seeds:{}'.format(ty))


def get_seeds():
    def iterator():
        seed_types = r.keys('seeds:*')
        for st in seed_types:
            ty = st.replace('seeds:', '')
            for seed in list(r.smembers(st)):
                yield ty, base64.b64decode(seed)

    import collections

    result_dict = collections.defaultdict(list)
    for t, uri in iterator():
        result_dict[t].append(uri)
    return result_dict


def get_type_seeds(ty):
    try:
        t_dict = index.get_type(ty)
        all_seeds = set([])
        for t in t_dict['sub'] + [ty]:
            all_seeds.update([base64.b64decode(seed) for seed in list(r.smembers('seeds:{}'.format(t)))])
        return list(all_seeds)
    except TypeError:
        # Check if it is a property...and return an empty list
        try:
            index.get_property(ty)
            return []
        except TypeError:
            raise TypeNotAvailableError(ty)
