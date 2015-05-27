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

from agora_fountain.index import core as index
from agora_fountain.util import ThreadPool
from datetime import datetime as dt, timedelta as delta

def build_property_paths(prop):
    domain = index.get_property(prop).get('domain')
    paths = []
    for ty in domain:
        path = [{'type': ty, 'property': prop}]
        refs = index.get_type(ty).get('refs')
        if not len(refs):
            paths.append(path)
        for r in refs:
            sub_paths = build_property_paths(r)
            for sp in sub_paths:
                new_path = path[:]
                new_path.extend(sp)
                paths.append(new_path)

    return paths


def build_type_paths(ty):
    def build_path(refs):
        for r in refs:
            yield build_property_paths(r)

    paths = []
    type_rep = index.get_type(ty)
    ty_refs = type_rep.get('refs')
    for p in build_path(ty_refs):
        paths.extend(p)

    for sub in type_rep.get('sub'):
        refs = index.get_type(sub).get('refs')
        for p in build_path(refs):
            paths.extend(p)

    return paths


def calculate_paths():
    print 'calculating paths...',
    start_time = dt.now()
    elm_paths = list(__calculate_paths(index.get_properties(), index.get_types()))
    print 'Done (in {}ms)'.format((dt.now() - start_time).total_seconds() * 1000)

    locks = lock_key_pattern('paths:*')
    keys = [k for (k, _) in locks]
    if len(keys):
        index.r.delete(*keys)

    with index.r.pipeline() as pipe:
        pipe.multi()
        for (elm, paths) in elm_paths:
            print '{} paths for {}'.format(len(paths), elm)
            for (i, path) in enumerate(paths):
                pipe.set('paths:{}:{}'.format(elm, i), path)
        pipe.execute()

    for _, l in locks:
        l.release()

    print 'total paths = {}'.format(len(index.r.keys('paths:*')))


def lock_key_pattern(pattern):
    pattern_keys = index.r.keys(pattern)
    for k in pattern_keys:
        yield k, index.r.lock(k)

def build_paths(elm, dest):
    res = build_property_paths(elm)
    if len(res):
        dest.append((elm, res))


def __calculate_paths(properties, types):
    tpool = ThreadPool(50)
    paths = []
    for p in properties + types:
        tpool.add_task(build_paths, p, paths)
    tpool.wait_completion()
    return paths



