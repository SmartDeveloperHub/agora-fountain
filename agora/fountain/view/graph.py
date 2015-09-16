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
import itertools

from agora.fountain.index import core as index
from agora.fountain.index.paths import pgraph
from agora.fountain.index import seeds


def view_graph():
    """

    :return:
    """
    types, nodes, edges, roots = [], [], [], []

    ibase = 0
    nodes_dict = dict([(nid, base64.b16encode(nid)) for nid in pgraph.nodes()])
    for (nid, data) in pgraph.nodes(data=True):
        if data.get('ty') == 'type':
            types.append(nid)
            has_seeds = len(seeds.get_type_seeds(nid))
            node_d = {'data': {'id': nodes_dict[nid], 'label': nid, 'shape': 'roundrectangle',
                               'width': len(nid) * 10}}
            if has_seeds:
                roots.append(nodes_dict[nid])
                node_d['classes'] = 'seed'
            nodes.append(node_d)
            ibase += 1
        elif data.get('ty') == 'prop' and data.get('object'):
            dom = [t for (t, _) in pgraph.in_edges(nid)]
            ran = [t for (_, t) in pgraph.out_edges(nid)]
            dom = [d for d in dom if not set.intersection(set(index.get_type(d).get('super')), set(dom))]
            ran = [r for r in ran if not set.intersection(set(index.get_type(r).get('super')), set(ran))]

            op_edges = list(itertools.product(*[dom, ran]))
            edges.extend([{'data': {'id': 'e{}'.format(ibase + i), 'source': nodes_dict[s], 'label': nid + '\n\n',
                                    'target': nodes_dict[tg]}} for i, (s, tg) in enumerate(op_edges)])
            ibase += len(op_edges) + 1
        else:
            ran = data.get('range')
            if ran is None:
                print nid
            if len(ran):
                dom = [t for (t, _) in pgraph.in_edges(nid)]
                dom = [d for d in dom if not set.intersection(set(index.get_type(d).get('super')), set(dom))]
                dp_edges = list(itertools.product(*[dom, ran]))

                for i, (s, t) in enumerate(dp_edges):
                    rid = 'n{}'.format(len(nodes_dict) + len(nodes))
                    nodes.append({'data': {'id': rid, 'label': t, 'width': len(t) * 10, 'shape': 'ellipse'}})
                    edges.append(
                        {'data': {'id': 'e{}'.format(ibase + i), 'source': nodes_dict[s], 'label': nid + '\n\n',
                                  'target': rid}})
                ibase += len(dp_edges) + 1

    for t in types:
        super_types = index.get_type(t).get('super')
        super_types = [s for s in super_types if not set.intersection(set(index.get_type(s).get('sub')),
                                                                      set(super_types))]
        st_edges = [{'data': {'id': 'e{}'.format(ibase + i), 'source': nodes_dict[st], 'label': '',
                              'target': nodes_dict[t]}, 'classes': 'subclass'}
                    for i, st in enumerate(super_types) if st in nodes_dict]
        if len(st_edges):
            edges.extend(st_edges)

        ibase += len(st_edges) + 1

    return nodes, edges, roots
