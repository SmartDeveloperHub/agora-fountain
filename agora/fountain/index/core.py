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
from redis.exceptions import RedisError, BusyLoadingError

__author__ = 'Fernando Serena'

import redis
import agora.fountain.vocab.schema as sch
from agora.fountain.exceptions import FountainError
import agora.fountain.vocab.onto as vocs
from datetime import datetime as dt
from concurrent.futures.thread import ThreadPoolExecutor
import logging
from agora.fountain.server import app
import sys
import multiprocessing

log = logging.getLogger('agora.fountain.index')

redis_conf = app.config['REDIS']
pool = redis.ConnectionPool(host=redis_conf.get('host'), port=redis_conf.get('port'), db=redis_conf.get('db'))
r = redis.StrictRedis(connection_pool=pool)
tpool = ThreadPoolExecutor(multiprocessing.cpu_count())

# Ping redis to check if it's ready
requests = 0
while True:
    try:
        r.keys('*')
        break
    except BusyLoadingError as re:
        log.warning(re.message)
    except RedisError:
        print 'Redis is not available'
        sys.exit(-1)

store_mode = app.config['STORE']
if 'memory' in store_mode:
    r.flushdb()


def __get_by_pattern(pattern, func):
    """

    :param pattern:
    :param func:
    :return:
    """
    def get_all():
        for k in pkeys:
            yield func(k)

    try:
        pkeys = r.keys(pattern)
        return list(get_all())
    except RedisError as e:
        raise FountainError(e.message)


def __remove_from_sets(values, *args):
    """

    :param values:
    :param args:
    :return:
    """
    try:
        for pattern in args:
            keys = r.keys(pattern)
            for dk in keys:
                key_parts = dk.split(':')
                ef_values = values
                if len(key_parts) > 1:
                    ef_values = filter(lambda x: x.split(':')[0] != key_parts[1], values)
                if len(ef_values):
                    r.srem(dk, *ef_values)
    except RedisError as e:
        raise FountainError(e.message)


def __get_vocab_set(pattern, vid=None):
    """

    :param pattern:
    :param vid:
    :return:
    """
    try:
        if vid is not None:
            pattern = pattern.replace(':*:', ':%s:' % vid)
        all_sets = map(lambda x: r.smembers(x), r.keys(pattern))
        return list(reduce(set.union, all_sets, set([])))
    except RedisError as e:
        raise FountainError(e.message)


def __extract_type(t, vid):
    """

    :param t:
    :param vid:
    :return:
    """
    log.debug('Extracting type {} from the {} vocabulary...'.format(t, vid))
    try:
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
    except RedisError as e:
        raise FountainError(e.message)


def __extract_property(p, vid):
    """

    :param p:
    :param vid:
    :return:
    """
    def p_type():
        if sch.is_object_property(p):
            return 'object'
        else:
            return 'data'

    try:
        log.debug('Extracting property {} from the {} vocabulary...'.format(p, vid))
        with r.pipeline() as pipe:
            pipe.multi()
            pipe.sadd('vocabs:{}:properties'.format(vid), p)
            pipe.hset('vocabs:{}:properties:{}'.format(vid, p), 'uri', p)
            for dc in list(sch.get_property_domain(p)):
                pipe.sadd('vocabs:{}:properties:{}:_domain'.format(vid, p), dc)
            for dc in list(sch.get_property_range(p)):
                pipe.sadd('vocabs:{}:properties:{}:_range'.format(vid, p), dc)
            for dc in list(sch.get_property_inverses(p)):
                pipe.sadd('vocabs:{}:properties:{}:_inverse'.format(vid, p), dc)
            pipe.set('vocabs:{}:properties:{}:_type'.format(vid, p), p_type())
            pipe.execute()
    except RedisError as e:
        raise FountainError(e.message)


def __extract_types(vid):
    """

    :param vid:
    :return:
    """
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
    # TODO: Catch exceptions from threadpool
    for v, t in types:
        futures.append(tpool.submit(__extract_type, t, v))
    for v, p in dependent_props:
        futures.append(tpool.submit(__extract_property, p, v))
    return types, futures


def __extract_properties(vid):
    """

    :param vid:
    :return:
    """
    properties = sch.get_properties(vid)

    other_vocabs = filter(lambda x: x != vid, vocs.get_vocabularies())
    dependent_types = set([])
    for ovid in other_vocabs:
        o_types = [t for t in get_types(ovid)]
        for oty in o_types:
            o_type = get_type(oty)
            if set.intersection(properties, o_type.get('refs')) or set.intersection(properties, o_type.get('properties')):
                dependent_types.add((ovid, oty))

    futures = []
    for p in properties:
        futures.append(tpool.submit(__extract_property, p, vid))
    for v, ty in dependent_types:
        futures.append(tpool.submit(__extract_type, ty, v))
    return properties, futures


def delete_vocabulary(vid):
    """

    :param vid:
    :return:
    """
    v_types = get_types(vid)
    if len(v_types):
        __remove_from_sets(v_types, '*:_domain', '*:_range', '*:sub', '*:super')
    v_props = get_properties(vid)
    if len(v_props):
        __remove_from_sets(v_props, '*:refs', '*:props')
    try:
        v_keys = r.keys('vocabs:{}:*'.format(vid))
        if len(v_keys):
            r.delete(*v_keys)
    except RedisError as e:
        raise FountainError(e.message)


def extract_vocabulary(vid):
    """

    :param vid:
    :return:
    """
    log.info('Extracting vocabulary {}...'.format(vid))
    delete_vocabulary(vid)
    start_time = dt.now()
    types, t_futures = __extract_types(vid)
    properties, p_futures = __extract_properties(vid)
    for f in t_futures + p_futures:
        f.result()
    log.info('Done (in {}ms)'.format((dt.now() - start_time).total_seconds() * 1000))
    return types, properties


def get_types(vid=None):
    """

    :param vid:
    :return:
    """
    def shared_type(t):
        return any(filter(lambda k: r.sismember(k, t), all_type_keys))

    vid_types = __get_vocab_set('vocabs:*:types', vid)

    if vid is not None:
        all_type_keys = filter(lambda k: k != 'vocabs:{}:types'.format(vid), r.keys("vocabs:*:types"))
        vid_types = filter(lambda t: not shared_type(t), vid_types)

    return vid_types


def get_properties(vid=None):
    """

    :param vid:
    :return:
    """
    def shared_property(t):
        return any(filter(lambda k: r.sismember(k, t), all_prop_keys))

    vid_props = __get_vocab_set('vocabs:*:properties', vid)

    if vid is not None:
        all_prop_keys = filter(lambda k: k != 'vocabs:{}:properties'.format(vid), r.keys("vocabs:*:properties"))
        vid_props = filter(lambda t: not shared_property(t), vid_props)

    return vid_props


def get_property(prop):
    """

    :param prop:
    :return:
    """
    def get_inverse_domain(ip):
        return reduce(set.union, __get_by_pattern('*:properties:{}:_domain'.format(ip), r.smembers), set([]))

    def get_inverse_range(ip):
        return reduce(set.union, __get_by_pattern('*:properties:{}:_range'.format(ip), r.smembers), set([]))

    all_prop_keys = r.keys('*:properties')
    if not filter(lambda k: r.sismember(k, prop), all_prop_keys):
        raise TypeError('Unknown property')

    domain = reduce(set.union, __get_by_pattern('*:properties:{}:_domain'.format(prop), r.smembers), set([]))
    rang = reduce(set.union, __get_by_pattern('*:properties:{}:_range'.format(prop), r.smembers), set([]))
    inv = reduce(set.union, __get_by_pattern('*:properties:{}:_inverse'.format(prop), r.smembers), set([]))

    if len(inv):
        inverse_dr = [(get_inverse_domain(i), get_inverse_range(i)) for i in inv]
        for dom, ra in inverse_dr:
            domain.update(ra)
            rang.update(dom)

    ty = __get_by_pattern('*:properties:{}:_type'.format(prop), r.get)
    try:
        ty = ty.pop()
    except IndexError:
        ty = 'object'

    return {'domain': list(domain), 'range': list(rang), 'inverse': list(inv), 'type': ty}


def is_property(prop):
    """

    :param prop:
    :return:
    """
    try:
        return len(r.keys('*:properties:{}:*'.format(prop)))
    except RedisError as e:
        raise FountainError(e.message)


def is_type(ty):
    """

    :param ty:
    :return:
    """
    try:
        return len(r.keys('*:types:{}:*'.format(ty)))
    except RedisError as e:
        raise FountainError(e.message)


def get_type(ty):
    """

    :param ty:
    :return:
    """
    try:
        all_type_keys = r.keys('*:types')
        if not filter(lambda k: r.sismember(k, ty), all_type_keys):
            raise TypeError('Unknown type')

        super_types = reduce(set.union, __get_by_pattern('*:types:{}:super'.format(ty), r.smembers), set([]))
        sub_types = reduce(set.union, __get_by_pattern('*:types:{}:sub'.format(ty), r.smembers), set([]))
        type_props = reduce(set.union, __get_by_pattern('*:types:{}:props'.format(ty), r.smembers), set([]))
        type_refs = reduce(set.union, __get_by_pattern('*:types:{}:refs'.format(ty), r.smembers), set([]))

        return {'super': list(super_types),
                'sub': list(sub_types),
                'properties': list(type_props),
                'refs': list(type_refs)}
    except RedisError as e:
        raise FountainError(e.message)
