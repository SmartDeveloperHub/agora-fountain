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

import logging
from agora_fountain.index import core as index
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime as dt
import networkx as nx

log = logging.getLogger('agora_fountain.paths')

pgraph = nx.DiGraph()
rgraph = nx.DiGraph()

def build_directed_graph():
    pgraph.clear()
    rgraph.clear()

    pgraph.add_nodes_from(index.get_types(), ty='type')
    for node in index.get_properties():
        p_dict = index.get_property(node)
        dom = p_dict.get('domain')
        ran = p_dict.get('range')
        edges = [(d, node) for d in dom]
        if p_dict.get('type') == 'object':
            edges.extend([(node, r) for r in ran])
        pgraph.add_edges_from(edges)
        pgraph.add_node(node, ty='prop', object=p_dict.get('type') == 'object', range=ran)
    for node in index.get_types():
        p_dict = index.get_type(node)
        refs = p_dict.get('refs')
        props = p_dict.get('properties')
        edges = [(r, node) for r in refs]
        edges.extend([(node, p) for p in props])
        pgraph.add_edges_from(edges)

    print 'graph', list(pgraph.edges())


def build_paths(node, root, steps=None):
    paths = []
    if steps is None:
        steps = []
    pred = pgraph.predecessors(node)
    # pred = [d for d in pred if not set.intersection(set(index.get_type(d).get('super')), set(pred))]
    for t in [x for x in pred if x != root]:
        step = {'property': node, 'type': t}
        if step in steps:
            continue
        path = [step]
        new_steps = steps[:]
        new_steps.append(step)
        for p in pgraph.predecessors(t):
            sub_paths = build_paths(p, root, new_steps[:])
            for sp in sub_paths:
                paths.append(path + sp)
        if not len(paths):
            paths.append(path)

    return paths


def calculate_paths():
    def __calculate_node_paths(n, d):
        ty = d.get('ty')
        _paths = []
        if ty == 'type':
            for p in pgraph.predecessors(n):
                _paths.extend(build_paths(p, n))
            type_dict = index.get_type(n)
            for st in type_dict.get('sub'):
                for p in pgraph.predecessors(st):
                    _paths.extend(build_paths(p, st))
        else:
            _paths.extend(build_paths(n, n))
        log.debug('{} paths for {}'.format(len(_paths), n))
        return n, _paths

    log.info('Calculating paths...')
    start_time = dt.now()

    build_directed_graph()

    index.r.delete('cycles')
    g_cycles = list(nx.simple_cycles(pgraph))
    with index.r.pipeline() as pipe:
        pipe.multi()
        for i, cy in enumerate(g_cycles):
            print cy
            cycle = []
            t_cycle = None
            for elm in cy:
                if index.is_type(elm):
                    t_cycle = elm
                elif t_cycle is not None:
                    cycle.append({'property': elm, 'type': t_cycle})
                    t_cycle = None
            if t_cycle is not None:
                cycle.append({'property': cy[0], 'type': t_cycle})
            pipe.zadd('cycles', i, cycle)
        pipe.execute()

    locks = lock_key_pattern('paths:*')
    keys = [k for (k, _) in locks]
    if len(keys):
        index.r.delete(*keys)

    node_paths = []
    futures = []
    with ThreadPoolExecutor(1) as th_pool:
        for node, data in pgraph.nodes(data=True):
            futures.append(th_pool.submit(__calculate_node_paths, node, data))
        while len(futures):
            for f in futures:
                if f.done():
                    elm, res = f.result()
                    if len(res):
                        node_paths.append((elm, res))
                    futures.remove(f)
        th_pool.shutdown()

    with index.r.pipeline() as pipe:
        pipe.multi()
        for (elm, paths) in node_paths:
            for (i, path) in enumerate(paths):
                for step in path:
                    for j, c in enumerate(g_cycles):
                        if step.get('type') in c or step.get('property') in c:
                            pipe.sadd('cycles:{}'.format(elm), j)
                pipe.zadd('paths:{}'.format(elm), i, path)
        pipe.execute()

    for _, l in locks:
        l.release()

    log.info('Found {} paths in {}ms'.format(len(index.r.keys('paths:*')),
                                             (dt.now() - start_time).total_seconds() * 1000))


def lock_key_pattern(pattern):
    pattern_keys = index.r.keys(pattern)
    for k in pattern_keys:
        yield k, index.r.lock(k)


