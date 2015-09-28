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
import multiprocessing

from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures import wait, ALL_COMPLETED
import networkx as nx

from agora.fountain.index import core as index, seeds

log = logging.getLogger('agora.fountain.paths')

pgraph = nx.DiGraph()
match_elm_cycles = {}


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    if n:
        for i in xrange(0, len(l), n):
            yield l[i:i + n]


def __build_directed_graph(generic=False, graph=None):
    """

    :return:
    """
    if graph is None:
        graph = nx.DiGraph()
    else:
        graph.clear()

    graph.add_nodes_from(index.get_types(), ty='type')
    for node in index.get_properties():
        p_dict = index.get_property(node)
        dom = set(p_dict.get('domain'))
        if generic:
            dom = filter(lambda x: not set.intersection(set(index.get_type(x)['super']), dom), dom)
        ran = set(p_dict.get('range'))
        if generic:
            try:
                ran = filter(lambda x: not set.intersection(set(index.get_type(x)['super']), ran), ran)
            except TypeError:
                pass
        edges = [(d, node) for d in dom]
        if p_dict.get('type') == 'object':
            edges.extend([(node, r) for r in ran])
        graph.add_edges_from(edges)
        graph.add_node(node, ty='prop', object=p_dict.get('type') == 'object', range=ran)

    print 'graph', list(graph.edges())
    return graph


def __build_paths(node, root, steps=None, level=0, path_graph=None, cache=None):
    """

    :param node:
    :param root:
    :param steps:
    :return:
    """

    def get_property(p):
        if p not in cache:
            cache[p] = index.get_property(p)
        return cache[p]

    def contains_cycle(graph):
        return bool(list(nx.simple_cycles(graph)))

    paths = []
    if steps is None:
        steps = []
    if path_graph is None:
        path_graph = nx.DiGraph()
    if cache is None:
        cache = {}

    log.debug('[{}] building paths to {}, with root {} and {} previous steps'.format(level, node, root, len(steps)))

    pred = set(pgraph.predecessors(node))
    for t in [x for x in pred]:
        new_path_graph = path_graph.copy()
        new_path_graph.add_nodes_from([t, node])
        new_path_graph.add_edges_from([(t, node)])
        if contains_cycle(new_path_graph):
            continue

        step = {'property': node, 'type': t}
        path = [step]
        new_steps = steps[:]
        new_steps.append(step)
        log.debug('[{}] added a new step {} in the path to {}'.format(level, (t, node), node))

        try:
            node_inverse = get_property(node)['inverse']
        except TypeError:
            node_inverse = []

        any_subpath = False
        next_steps = [x for x in pgraph.predecessors(t) if x != root and x not in node_inverse]
        for p in next_steps:
            log.debug('[{}] following {} as a pred property of {}'.format(level, p, t))
            extended_new_path_graph = new_path_graph.copy()
            extended_new_path_graph.add_node(p)
            extended_new_path_graph.add_edges_from([(p, t)])
            if contains_cycle(extended_new_path_graph):
                continue
            sub_paths = __build_paths(p, root, new_steps[:], level=level + 1, path_graph=extended_new_path_graph,
                                      cache=cache)

            any_subpath = any_subpath or len(sub_paths)
            for sp in sub_paths:
                paths.append(path + sp)
        if (len(next_steps) and not any_subpath) or not len(next_steps):
            paths.append(path)

    log.debug('[{}] returning {} paths to {}, with root {} and {} previous steps'.format(level, len(paths), node, root,
                                                                                         len(steps)))
    return paths


def calculate_paths():
    """

    :return:
    """
    def __find_matching_cycles(_elm):
        for j, c in enumerate(g_cycles):
            extended_elm = [_elm]
            if index.is_type(_elm):
                extended_elm.extend(index.get_type(_elm)["super"])

            if len([c for e in extended_elm if e in c]):
                yield j

    def __store_path(_i, _path):
        pipe.zadd('paths:{}'.format(elm), _i, _path)

    def __calculate_node_paths(n, d):
        log.debug('[START] Calculating paths to {} with data {}'.format(n, d))
        _paths = []
        if d.get('ty') == 'type':
            for p in pgraph.predecessors(n):
                log.debug('Following root [{}] predecessor property {}'.format(n, p))
                _paths.extend(__build_paths(p, n))
        else:
            _paths.extend(__build_paths(n, n))
        log.debug('[END] {} paths for {}'.format(len(_paths), n))
        if len(_paths):
            node_paths[n] = _paths

    log.info('Calculating paths...')
    match_elm_cycles.clear()
    start_time = dt.now()

    __build_directed_graph(graph=pgraph)
    g_graph = __build_directed_graph(generic=True)

    cycle_keys = index.r.keys('*cycles*')
    for ck in cycle_keys:
        index.r.delete(ck)
    g_cycles = list(nx.simple_cycles(g_graph))
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

    node_paths = {}
    futures = []
    with ThreadPoolExecutor(multiprocessing.cpu_count()) as th_pool:
        for node, data in pgraph.nodes(data=True):
            futures.append(th_pool.submit(__calculate_node_paths, node, data))
        wait(futures, timeout=None, return_when=ALL_COMPLETED)
        th_pool.shutdown()

    for ty in [_ for _ in index.get_types() if _ in node_paths]:
        for sty in [_ for _ in index.get_type(ty)['sub'] if _ in node_paths]:
            node_paths[ty].extend(node_paths[sty])

    node_paths = node_paths.items()

    print 'preparing to persist the calculated paths...{}'.format(len(node_paths))

    with index.r.pipeline() as pipe:
        pipe.multi()
        with ThreadPoolExecutor(multiprocessing.cpu_count()) as th_pool:
            for (elm, paths) in node_paths:
                futures = []
                for (i, path) in enumerate(paths):
                    futures.append(th_pool.submit(__store_path, i, path))
                    for step in path:
                        step_ty = step.get('type')
                        if step_ty not in match_elm_cycles:
                            match_elm_cycles[step_ty] = __find_matching_cycles(step_ty)
                        step_pr = step.get('property')
                        if step_pr not in match_elm_cycles:
                            match_elm_cycles[step_pr] = __find_matching_cycles(step_pr)
                wait(futures, timeout=None, return_when=ALL_COMPLETED)
                pipe.execute()
            th_pool.shutdown()

        # Store type and property cycles
        for elm in match_elm_cycles.keys():
            for c in match_elm_cycles[elm]:
                pipe.sadd('cycles:{}'.format(elm), c)
        pipe.execute()
        for t in [_ for _ in index.get_types() if _ not in match_elm_cycles]:
            for c in __find_matching_cycles(t):
                pipe.sadd('cycles:{}'.format(t), c)
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
            if end_index >= len(steps_copy):
                cand_cycle.extend(steps_copy[:end_index - len(steps_copy)])
            if cand_cycle == cycle:
                steps_copy = steps[0:start_index - end_index + len(steps_copy)]
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
    seed_av = {}

    def check_seed_availability(ty):
        if ty not in seed_av:
            seed_av[ty] = seeds.get_type_seeds(ty)
        return seed_av[ty]

    def filter_path_cycles(_seeds):
        """

        :param _seeds:
        :return:
        """
        sub_steps = list(reversed(path[:step_index + 1]))
        for _step in sub_steps:
            cycle_ids.update([int(c) for c in index.r.smembers('cycles:{}'.format(_step.get('type')))])
        cycles = [eval(index.r.zrangebyscore('cycles', c, c).pop()) for c in cycle_ids]
        sub_path = {'cycles': list(cycle_ids), 'seeds': _seeds, 'steps': sub_steps}

        for cycle in sorted(cycles, key=lambda x: len(x), reverse=True):  # First filter bigger cycles
            sub_steps = __detect_and_remove_cycles(cycle, sub_steps)
        sub_path['steps'] = sub_steps
        if sub_path not in seed_paths:
            seed_paths.append(sub_path)
        return cycle_ids

    seed_paths = []
    paths = [(int(score), eval(path)) for path, score in index.r.zrange('paths:{}'.format(elm), 0, -1, withscores=True)]

    applying_cycles = set([])
    cycle_ids = set([int(c) for c in index.r.smembers('cycles:{}'.format(elm))])

    step_index = 0
    for score, path in paths:
        for step_index, step in enumerate(path):
            ty = step.get('type')
            type_seeds = check_seed_availability(ty)
            if len(type_seeds):
                seed_cycles = filter_path_cycles(type_seeds)
                applying_cycles = applying_cycles.union(set(seed_cycles))

    # It only returns seeds if elm is a type and there are seeds of it
    req_type_seeds = check_seed_availability(elm)
    if len(req_type_seeds):
        path = []
        seed_cycles = filter_path_cycles(req_type_seeds)
        applying_cycles = applying_cycles.union(set(seed_cycles))

    applying_cycles = [{'cycle': int(cid), 'steps': eval(index.r.zrange('cycles', cid, cid).pop())} for cid in
                       applying_cycles]
    return list(seed_paths), applying_cycles


# Build the current graph on import
__build_directed_graph(graph=pgraph)
