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
from datetime import datetime as dt

from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures import wait, ALL_COMPLETED
import networkx as nx

from agora.fountain.index import core as index, seeds

log = logging.getLogger('agora.fountain.paths')

pgraph = nx.DiGraph()


def __build_directed_graph():
    """

    :return:
    """
    pgraph.clear()

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


def __build_paths(node, root, steps=None):
    """

    :param node:
    :param root:
    :param steps:
    :return:
    """
    paths = []
    if steps is None:
        steps = []
    pred = pgraph.predecessors(node)
    for t in [x for x in pred if x != root or not steps]:
        step = {'property': node, 'type': t}
        if step in steps:
            continue
        path = [step]
        new_steps = steps[:]
        new_steps.append(step)
        for p in pgraph.predecessors(t):
            sub_paths = __build_paths(p, root, new_steps[:])
            for sp in sub_paths:
                paths.append(path + sp)
        if not len(paths):
            paths.append(path)

    return paths


def calculate_paths():
    """

    :return:
    """
    def __calculate_node_paths(n, d):
        ty = d.get('ty')
        _paths = []
        if ty == 'type':
            for p in pgraph.predecessors(n):
                _paths.extend(__build_paths(p, n))
            type_dict = index.get_type(n)
            for st in type_dict.get('sub'):
                for p in pgraph.predecessors(st):
                    _paths.extend(__build_paths(p, st))
        else:
            _paths.extend(__build_paths(n, n))
        log.debug('{} paths for {}'.format(len(_paths), n))
        return n, _paths

    log.info('Calculating paths...')
    start_time = dt.now()

    __build_directed_graph()

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

    locks = __lock_key_pattern('paths:*')
    keys = [k for (k, _) in locks]
    if len(keys):
        index.r.delete(*keys)

    node_paths = []
    futures = []
    with ThreadPoolExecutor(8) as th_pool:
        for node, data in pgraph.nodes(data=True):
            futures.append(th_pool.submit(__calculate_node_paths, node, data))
        wait(futures, timeout=None, return_when=ALL_COMPLETED)
        for f in futures:
            if f.done():
                elm, res = f.result()
                if len(res):
                    node_paths.append((elm, res))
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
        pipe.execute()

    for _, l in locks:
        l.release()

    log.info('Found {} paths in {}ms'.format(len(index.r.keys('paths:*')),
                                             (dt.now() - start_time).total_seconds() * 1000))


def __lock_key_pattern(pattern):
    """

    :param pattern:
    :return:
    """
    pattern_keys = index.r.keys(pattern)
    for k in pattern_keys:
        yield k, index.r.lock(k)


def __detect_and_remove_cycles(cycle, steps):
    """

    :param cycle:
    :param steps:
    :return:
    """
    if cycle[0] in steps:
        steps_copy = steps[:]
        start_index = steps_copy.index(cycle[0])
        end_index = start_index + len(cycle)
        try:
            cand_cycle = steps_copy[start_index:end_index]
            if cand_cycle == cycle:
                steps_copy = steps[0:start_index]
                if len(steps) > end_index:
                    steps_copy += steps[end_index:]
        except IndexError:
            pass
        return steps_copy
    return steps


def find_path(elm):
    """

    :param elm:
    :return:
    """
    def filter_path_cycles(_seeds):
        """

        :param _seeds:
        :return:
        """
        cycle_ids = [int(c) for c in index.r.smembers('cycles:{}'.format(elm))]
        sub_steps = list(reversed(path[:step_index + 1]))
        sub_path = {'cycles': cycle_ids, 'seeds': _seeds, 'steps': sub_steps}
        cycles = [eval(index.r.zrangebyscore('cycles', c, c).pop()) for c in cycle_ids]
        for cycle in sorted(cycles, key=lambda x: len(x), reverse=True):  # First filter bigger cycles
            sub_steps = __detect_and_remove_cycles(cycle, sub_steps)
        sub_path['steps'] = sub_steps
        if sub_path not in seed_paths:
            seed_paths.append(sub_path)
        return cycle_ids

    paths = []
    seed_paths = []
    for path, score in index.r.zrange('paths:{}'.format(elm), 0, -1, withscores=True):
        paths.append((int(score), eval(path)))

    applying_cycles = set([])

    step_index = 0
    for score, path in paths:
        for step_index, step in enumerate(path):
            ty = step.get('type')
            type_seeds = seeds.get_type_seeds(ty)
            if len(type_seeds):
                seed_cycles = filter_path_cycles(type_seeds)
                applying_cycles = applying_cycles.union(set(seed_cycles))

    # It only returns seeds if elm is a type and there are seeds of it
    req_type_seeds = seeds.get_type_seeds(elm)
    if len(req_type_seeds):
        path = []
        seed_cycles = filter_path_cycles(req_type_seeds)
        applying_cycles = applying_cycles.union(set(seed_cycles))

    applying_cycles = [{'cycle': int(cid), 'steps': eval(index.r.zrange('cycles', cid, cid).pop())} for cid in
                       applying_cycles]
    return list(seed_paths), applying_cycles


# Build the current graph on import
__build_directed_graph()
