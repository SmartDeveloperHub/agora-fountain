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
import itertools

log = logging.getLogger('agora_fountain.paths')

pgraph = nx.DiGraph()

def build_property_paths(prop, steps=None, last_cycle=None):
    if steps is None:
        steps = []
    domain = index.get_property(prop).get('domain')
    paths = []
    for ty in domain:
        step = {'type': ty, 'property': prop}
        path = [step]
        if step == last_cycle:
            log.warning('cycle detected on {}'.format(step))
            last_cycle = None
            continue
        if step in steps and last_cycle is None:
            last_cycle = step.copy()
            steps[-1]['cycle'] = len(steps) - steps.index(step) - 1
            cycle_path = steps[:]
            cycle_path[-1]['end'] = True
            paths.append(cycle_path)
        refs = index.get_type(ty).get('refs')
        refs = filter(lambda x: prop not in index.get_property(x).get('inverse'), refs)
        if not len(refs):
            paths.append(path)
        else:
            for r in refs:
                sub_paths = build_property_paths(r, steps + path, last_cycle=last_cycle)
                for sp in sub_paths:
                    if not sp[-1].get('end', False):
                        paths.append(path + sp)
                    else:
                        paths.append(sp)
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

def build_directed_graph():
    pgraph.clear()
    pgraph.add_nodes_from(index.get_types(), ty='type')
    for node in index.get_properties():
        p_dict = index.get_property(node)
        dom = p_dict.get('domain')
        ran = p_dict.get('range')
        edges = [(node, d) for d in dom]
        edges.extend([(r, node) for r in ran])
        # edges = list(itertools.product(*[dom, ran]))
        pgraph.add_edges_from(edges)
    pgraph.add_nodes_from(index.get_properties(), ty='prop')
    for node in index.get_types():
        p_dict = index.get_type(node)
        refs = p_dict.get('refs')
        props = p_dict.get('properties')
        # edges = list(itertools.product(*[refs, props]))
        edges = [(node, r) for r in refs]
        edges.extend([(p, node) for p in props])

        pgraph.add_edges_from(edges)

    print 'graph', list(pgraph.edges())


def build_paths(node, tree, pred=False):
    paths = []

    props = tree.successors(node)
    for p in props:
        next_types = tree.successors(p)
        for t in next_types:
            step = {'property': p, 'type': t}
            path = [step]
            sub_paths = build_paths(t, tree)
            if not len(sub_paths):
                paths.append(path)
            for sp in sub_paths:
                paths.append(path + sp)

    # if pred:
    #     pred = pgraph.predecessors(node)
    #     for tpr in pred:
    #         for path in paths:
    #             path.insert(0, {'property': node, 'type': tpr})

    return paths


def calculate_paths():
    log.info('Calculating paths...')
    start_time = dt.now()

    build_directed_graph()

    # print list(nx.simple_cycles(pgraph))

    locks = lock_key_pattern('paths:*')
    keys = [k for (k, _) in locks]
    if len(keys):
        index.r.delete(*keys)

    node_paths = []
    for node, data in pgraph.nodes(data=True):
        ty = data.get('ty')
        node_tree = nx.bfs_tree(pgraph, node)
        print 'bfs tree for {}'.format(node), list(node_tree.edges())
        paths = []
        if ty == 'type':
            paths.extend(build_paths(node, node_tree))
            # Add subclasses
        # else:
        #     succ = pgraph.successors(node)
        #     for s in succ:
        #         paths.extend(build_paths(s, node_tree, pred=True))

        if len(paths):
            node_paths.append((node, paths))

    with index.r.pipeline() as pipe:
        pipe.multi()
        for (elm, paths) in node_paths:
            log.debug('{} paths for {}'.format(len(paths), elm))
            for (i, path) in enumerate(paths):
                try:
                    del path[-1]['end']
                except KeyError:
                    pass
                pipe.set('paths:{}:{}'.format(elm, i), path)
        pipe.execute()

    for _, l in locks:
        l.release()

    log.info('Found {} paths in {}ms'.format(len(index.r.keys('paths:*')),
                                             (dt.now() - start_time).total_seconds() * 1000))

    # start_time = dt.now()
    # elm_paths = list(__calculate_paths(index.get_properties(), index.get_types()))
    #
    # locks = lock_key_pattern('paths:*')
    # keys = [k for (k, _) in locks]
    # if len(keys):
    #     index.r.delete(*keys)
    #
    # with index.r.pipeline() as pipe:
    #     pipe.multi()
    #     for (elm, paths) in elm_paths:
    #         log.debug('{} paths for {}'.format(len(paths), elm))
    #         for (i, path) in enumerate(paths):
    #             try:
    #                 del path[-1]['end']
    #             except KeyError:
    #                 pass
    #             pipe.set('paths:{}:{}'.format(elm, i), path)
    #     pipe.execute()
    #
    # for _, l in locks:
    #     l.release()
    #
    # log.info('Found {} paths in {}ms'.format(len(index.r.keys('paths:*')),
    #                                          (dt.now() - start_time).total_seconds() * 1000))


def lock_key_pattern(pattern):
    pattern_keys = index.r.keys(pattern)
    for k in pattern_keys:
        yield k, index.r.lock(k)

def __calculate_type_paths(elm):
    return elm, build_type_paths(elm)

def __calculate_property_paths(elm):
    return elm, build_property_paths(elm)


def __calculate_paths(properties, types):
    paths = []
    futures = []
    with ThreadPoolExecutor(1) as pool:
        for p in properties:
            futures.append(pool.submit(__calculate_property_paths, p))
        for t in types:
            futures.append(pool.submit(__calculate_type_paths, t))
        while len(futures):
            for f in futures:
                if f.done():
                    elm, res = f.result()
                    if len(res):
                        paths.append((elm, res))
                    futures.remove(f)
        pool.shutdown()
    return paths



