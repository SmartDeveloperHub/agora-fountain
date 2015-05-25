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

import redis
from agora_fountain.vocab.schema import Schema
from functools import wraps
import base64


pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
r = redis.StrictRedis(connection_pool=pool)
pipe = r.pipeline()
sch = Schema()

r.flushall()


# Populate the database with the ontology types and properties
# print 'Analysing the ontology and populating the database...'
#
# print 'Collecting type descriptions:'
# for t in sch.types:
#     print 'type {}:'.format(t)
#     pipe.sadd('types', t)
#     t_supertypes = sch.get_supertypes(t)
#     for s in t_supertypes:
#         pipe.sadd('types:{}:super'.format(t), s)
#         print '\tsupertype {}'.format(s)
#     t_subtypes = sch.get_subtypes(t)
#     for s in t_subtypes:
#         pipe.sadd('types:{}:sub'.format(t), s)
#         print '\tsubtype {}'.format(s)
#     t_properties = sch.get_type_properties(t)
#     for s in t_properties:
#         pipe.sadd('types:{}:props'.format(t), s)
#         print '\tproperty {}'.format(s)
#     t_incomes = sch.get_type_references(t)
#     for s in t_incomes:
#         pipe.sadd('types:{}:refs'.format(t), s)
#         print '\tref {}'.format(s)
#     pipe.execute()
#
# print 'Collecting property descriptions:'
# for p in sch.properties:
#     print 'property {}:'.format(p)
#     pipe.sadd('properties', p)
#     pipe.hset('properties:{}'.format(p), 'uri', p)
#     p_domain = list(sch.get_property_domain(p))
#     for dc in p_domain:
#         print '\tdomain {}'.format(dc)
#         pipe.sadd('properties:{}:domain'.format(p), dc)
#
#     p_range = list(sch.get_property_range(p))
#     for dc in p_range:
#         print '\trange {}'.format(dc)
#         pipe.sadd('properties:{}:range'.format(p), dc)
#     type_value = 'data'
#     if sch.is_object_property(p):
#         type_value = 'object'
#     print '\ttype {}'.format(type_value)
#     pipe.set('properties:{}:type'.format(p), type_value)
#     pipe.execute()


def get_types():
    return list(r.smembers('types'))


def get_properties():
    return list(r.smembers('properties'))


def get_seeds():
    def iterator():
        seed_types = r.keys('seeds:*')
        for st in seed_types:
            for seed in list(r.smembers(st)):
                yield base64.b64decode(seed)
    return list(iterator())


def get_type_seeds(ty):
    return [base64.b64decode(seed) for seed in list(r.smembers('seeds:{}'.format(ty)))]


def get_property(prop):
    db = redis.StrictRedis(connection_pool=pool)
    domain = db.smembers('properties:{}:domain'.format(prop))
    rang = db.smembers('properties:{}:range'.format(prop))
    ty = db.get('properties:{}:type'.format(prop))

    return {'domain': list(domain), 'range': list(rang), 'type': ty}


def get_type(ty):
    db = redis.StrictRedis(connection_pool=pool)
    super_types = db.smembers('types:{}:super'.format(ty))
    sub_types = db.smembers('types:{}:sub'.format(ty))
    type_props = db.smembers('types:{}:props'.format(ty))
    type_refs = db.smembers('types:{}:refs'.format(ty))

    return {'super': list(super_types),
            'sub': list(sub_types),
            'properties': list(type_props),
            'refs': list(type_refs)}


def add_seed(uri, ty):
    if r.sismember('types', ty):
        r.sadd('seeds:{}'.format(ty), base64.b64encode(uri))
