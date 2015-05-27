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
import base64
from agora_fountain.util import ThreadPool
from datetime import datetime


pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
r = redis.StrictRedis(connection_pool=pool)

r.flushall()

def get_by_pattern(pattern, func):
    def get_all():
        for k in pkeys:
            yield func(k)
    pkeys = r.keys(pattern)
    return list(get_all())

def remove_from_sets(values, *args):
    for pattern in args:
        keys = r.keys(pattern)
        for dk in keys:
            key_parts = dk.split(':')
            ef_values = values
            if len(key_parts) > 1:
                ef_values = filter(lambda x: x.split(':')[0] != key_parts[1], values)
            if len(ef_values):
                r.srem(dk, *ef_values)


def delete_vocabulary(vid):
    v_types = get_types(vid)
    if len(v_types):
        remove_from_sets(v_types, '*:domain', '*:range', '*:sub', '*:super')
    v_props = get_properties(vid)
    if len(v_props):
        remove_from_sets(v_props, '*:refs', '*:props')
    v_keys = r.keys('vocabs:{}:*'.format(vid))
    if len(v_keys):
        r.delete(*v_keys)


def extract_vocabulary(vid):
    delete_vocabulary(vid)
    tpool = ThreadPool(1)
    pre = datetime.now()
    types = extract_types(vid, tpool)
    properties = extract_properties(vid, tpool)
    tpool.wait_completion()
    print datetime.now() - pre
    return types, properties

def extract_type(t, vid):
    print 'type {}'.format(t)
    sch = Schema()
    with r.pipeline() as pipe:
        pipe.multi()
        # pipe.sadd('types', t)
        pipe.sadd('vocabs:{}:types'.format(vid), t)
        t_supertypes = sch.get_supertypes(t)
        for s in t_supertypes:
            pipe.sadd('vocabs:{}:types:{}:super'.format(vid, t), s)
            # print '\tsupertype {}'.format(s)
        t_subtypes = sch.get_subtypes(t)
        for s in t_subtypes:
            pipe.sadd('vocabs:{}:types:{}:sub'.format(vid, t), s)
            # print '\tsubtype {}'.format(s)
        t_properties = sch.get_type_properties(t)
        for s in t_properties:
            pipe.sadd('vocabs:{}:types:{}:props'.format(vid, t), s)
            # print '\tproperty {}'.format(s)
        t_incomes = sch.get_type_references(t)
        for s in t_incomes:
            pipe.sadd('vocabs:{}:types:{}:refs'.format(vid, t), s)
            # print '\tref {}'.format(s)
        pipe.execute()

def extract_property(p, vid):
    print 'property {}'.format(p)
    sch = Schema()
    with r.pipeline() as pipe:
        pipe.multi()
        pipe.sadd('vocabs:{}:properties'.format(vid), p)
        pipe.hset('vocabs:{}:properties:{}'.format(vid, p), 'uri', p)
        p_domain = list(sch.get_property_domain(p))
        for dc in p_domain:
            # print '\tdomain {}'.format(dc)
            pipe.sadd('vocabs:{}:properties:{}:domain'.format(vid, p), dc)

        p_range = list(sch.get_property_range(p))
        for dc in p_range:
            # print '\trange {}'.format(dc)
            pipe.sadd('vocabs:{}:properties:{}:range'.format(vid, p), dc)
        type_value = 'data'
        if sch.is_object_property(p):
            type_value = 'object'
        # print '\ttype {}'.format(type_value)
        pipe.set('vocabs:{}:properties:{}:type'.format(vid, p), type_value)
        pipe.execute()

def extract_types(vid, tpool):
    sch = Schema()
    types = sch.get_types(vid)

    other_vocabs = filter(lambda x: x != vid, sch.get_vocabularies())
    dependent_types = set([])
    dependent_props = set([])
    for ovid in other_vocabs:
        o_types = [t for t in get_types(ovid) if t not in types]
        for oty in o_types:
            otype = get_type(oty)
            if set.intersection(types, otype.get('super')) or set.intersection(types, otype.get('sub')):
                dependent_types.add((ovid, oty))
        o_props = [t for t in get_properties(ovid)]
        for op in o_props:
            oprop = get_property(op)
            if set.intersection(types, oprop.get('domain')) or set.intersection(types, oprop.get('range')):
                dependent_props.add((ovid, op))

    types = set.union(set([(vid, t) for t in types]), dependent_types)
    for v, t in types:
        tpool.add_task(extract_type, t, v)
    for v, p in dependent_props:
        tpool.add_task(extract_property, p, v)
    return types

def extract_properties(vid, tpool):
    sch = Schema()
    properties = sch.get_properties(vid)

    other_vocabs = filter(lambda x: x != vid, sch.get_vocabularies())
    dependent_types = set([])
    for ovid in other_vocabs:
        o_types = [t for t in get_types(ovid)]
        for oty in o_types:
            otype = get_type(oty)
            if set.intersection(properties, otype.get('refs')) or set.intersection(properties, otype.get('properties')):
                dependent_types.add((ovid, oty))

    for p in properties:
        tpool.add_task(extract_property, p, vid)

    for v, ty in dependent_types:
        tpool.add_task(extract_type, ty, v)

    return properties


def __get_vocab_set(pattern, vid=None):
    if vid is not None:
        pattern = pattern.replace(':*:', ':%s:' % vid)
    all_sets = map(lambda x: r.smembers(x), r.keys(pattern))
    return list(reduce(set.union, all_sets, set([])))


def get_types(vid=None):
    return __get_vocab_set('vocabs:*:types', vid)


def get_properties(vid=None):
    return __get_vocab_set('vocabs:*:properties', vid)


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
    domain = reduce(set.union, get_by_pattern('*:properties:{}:domain'.format(prop), r.smembers), set([]))
    rang = reduce(set.union, get_by_pattern('*:properties:{}:range'.format(prop), r.smembers), set([]))
    ty = get_by_pattern('*:properties:{}:type'.format(prop), r.get)

    return {'domain': list(domain), 'range': list(rang), 'type': ty.pop()}


def get_type(ty):
    super_types = reduce(set.union, get_by_pattern('*:types:{}:super'.format(ty), r.smembers), set([]))
    sub_types = reduce(set.union, get_by_pattern('*:types:{}:sub'.format(ty), r.smembers), set([]))
    type_props = reduce(set.union, get_by_pattern('*:types:{}:props'.format(ty), r.smembers), set([]))
    type_refs = reduce(set.union, get_by_pattern('*:types:{}:refs'.format(ty), r.smembers), set([]))

    return {'super': list(super_types),
            'sub': list(sub_types),
            'properties': list(type_props),
            'refs': list(type_refs)}


def add_seed(uri, ty):
    type_keys = r.keys('*:types')
    for tk in type_keys:
        if r.sismember(tk, ty):
            r.sadd('seeds:{}'.format(ty), base64.b64encode(uri))
