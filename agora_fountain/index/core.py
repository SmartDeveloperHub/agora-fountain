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
import agora_fountain.vocab.schema as sch
import agora_fountain.vocab.onto as vocs
import base64
from datetime import datetime as dt
from concurrent.futures.thread import ThreadPoolExecutor
import logging
from agora_fountain.server import app

log = logging.getLogger('agora_fountain.index')

pool = redis.ConnectionPool(host=app.config['REDIS'], port=6379, db=0)
r = redis.StrictRedis(connection_pool=pool)
r.flushall()
tpool = ThreadPoolExecutor(20)

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
    log.info('Extracting vocabulary {}...'.format(vid))
    delete_vocabulary(vid)
    start_time = dt.now()
    types, t_futures = extract_types(vid)
    properties, p_futures = extract_properties(vid)
    for f in t_futures + p_futures:
        f.result()
    log.info('Done (in {}ms)'.format((dt.now() - start_time).total_seconds() * 1000))
    return types, properties


def extract_type(t, vid):
    # print 'type {}'.format(t),

    start_time = dt.now()
    with r.pipeline() as pipe:
        pipe.multi()
        pipe.sadd('vocabs:{}:types'.format(vid), t)
        for s in sch.get_supertypes(t):
            pipe.sadd('vocabs:{}:types:{}:super'.format(vid, t), s)
        for s in sch.get_subtypes(t):
            pipe.sadd('vocabs:{}:types:{}:sub'.format(vid, t), s)
        for s in sch.get_type_properties(t):
            pipe.sadd('vocabs:{}:types:{}:props'.format(vid, t), s)
        for s in sch.get_type_references(t):
            pipe.sadd('vocabs:{}:types:{}:refs'.format(vid, t), s)
        pipe.execute()

    # print '... in {}s'.format((dt.now() - start_time).total_seconds())


def extract_property(p, vid):
    def p_type():
        if sch.is_object_property(p):
            return 'object'
        else:
            return 'data'

    # print 'property {}'.format(p),
    start_time = dt.now()
    with r.pipeline() as pipe:
        pipe.multi()
        pipe.sadd('vocabs:{}:properties'.format(vid), p)
        pipe.hset('vocabs:{}:properties:{}'.format(vid, p), 'uri', p)
        for dc in list(sch.get_property_domain(p)):
            pipe.sadd('vocabs:{}:properties:{}:domain'.format(vid, p), dc)
        for dc in list(sch.get_property_range(p)):
            pipe.sadd('vocabs:{}:properties:{}:range'.format(vid, p), dc)
        for dc in list(sch.get_property_inverses(p)):
            pipe.sadd('vocabs:{}:properties:{}:inverse'.format(vid, p), dc)
        pipe.set('vocabs:{}:properties:{}:type'.format(vid, p), p_type())
        pipe.execute()
    # print '... in {}s'.format((dt.now() - start_time).total_seconds())


def extract_types(vid):
    types = sch.get_types(vid)

    other_vocabs = filter(lambda x: x != vid, vocs.get_vocabularies())
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
    futures = []
    for v, t in types:
        futures.append(tpool.submit(extract_type, t, v))
    for v, p in dependent_props:
        futures.append(tpool.submit(extract_property, p, v))
    return types, futures

def extract_properties(vid):
    properties = sch.get_properties(vid)

    other_vocabs = filter(lambda x: x != vid, vocs.get_vocabularies())
    dependent_types = set([])
    for ovid in other_vocabs:
        o_types = [t for t in get_types(ovid)]
        for oty in o_types:
            otype = get_type(oty)
            if set.intersection(properties, otype.get('refs')) or set.intersection(properties, otype.get('properties')):
                dependent_types.add((ovid, oty))

    futures = []
    for p in properties:
        futures.append(tpool.submit(extract_property, p, vid))
    for v, ty in dependent_types:
        futures.append(tpool.submit(extract_type, ty, v))
    return properties, futures


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
    def get_inverse_domain(ip):
        return reduce(set.union, get_by_pattern('*:properties:{}:domain'.format(ip), r.smembers), set([]))

    def get_inverse_range(ip):
        return reduce(set.union, get_by_pattern('*:properties:{}:range'.format(ip), r.smembers), set([]))

    domain = reduce(set.union, get_by_pattern('*:properties:{}:domain'.format(prop), r.smembers), set([]))
    rang = reduce(set.union, get_by_pattern('*:properties:{}:range'.format(prop), r.smembers), set([]))
    inv = reduce(set.union, get_by_pattern('*:properties:{}:inverse'.format(prop), r.smembers), set([]))

    if len(inv):
        inverse_dr = [(get_inverse_domain(i), get_inverse_range(i)) for i in inv]
        for dom, ra in inverse_dr:
            domain.update(ra)
            rang.update(dom)

    ty = get_by_pattern('*:properties:{}:type'.format(prop), r.get)
    try:
        ty = ty.pop()
    except IndexError:
        ty = 'object'

    return {'domain': list(domain), 'range': list(rang), 'inverse': list(inv), 'type': ty}


def is_property(prop):
    return len(r.keys('*:properties:{}:*'.format(prop)))

def is_type(ty):
    return len(r.keys('*:types:{}:*'.format(ty)))

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
