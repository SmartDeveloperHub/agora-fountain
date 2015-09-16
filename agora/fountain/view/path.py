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

from agora.fountain.index import core as index


def view_path(elm, paths):
    """

    :param elm:
    :param paths:
    :return:
    """
    nodes, edges, roots, mem_edges = [], [], set([]), set([])

    for path in paths:
        steps = path['steps']
        last_node = None
        last_prop = None
        for i, step in enumerate(steps):
            ty = step['type']
            prop = step['property']
            node_d = {'data': {'id': base64.b16encode(ty), 'label': ty, 'shape': 'roundrectangle',
                               'width': max(100, len(ty) * 12)}}
            if not i:
                roots.add(base64.b16encode(ty))
                node_d['classes'] = 'seed'

            nodes.append(node_d)
            if last_node is not None and (last_node, last_prop, ty) not in mem_edges:
                edges.append(
                    {'data': {'id': 'e{}'.format(len(edges)), 'source': base64.b16encode(last_node),
                              'label': last_prop + '\n\n\n',
                              'target': base64.b16encode(ty)}})
                mem_edges.add((last_node, last_prop, ty))
            last_node = ty
            last_prop = prop

        if index.is_type(elm):
            nodes.append({'data': {'id': base64.b16encode(elm), 'label': elm, 'shape': 'roundrectangle',
                                   'width': len(elm) * 10}, 'classes': 'end'})
            if (last_node, last_prop, elm) not in mem_edges:
                edges.append(
                    {'data': {'id': 'e{}'.format(len(edges)), 'source': base64.b16encode(last_node),
                              'label': last_prop + '\n\n\n',
                              'target': base64.b16encode(elm)}})
                mem_edges.add((last_node, last_prop, elm))
        else:
            prop = index.get_property(elm)
            prop_range = prop['range']
            prop_range = [d for d in prop_range if not set.intersection(set(index.get_type(d).get('super')),
                                                                        set(prop_range))]
            prop_type = prop['type']
            for r in prop_range:
                shape = 'roundrectangle'
                if prop_type == 'data':
                    shape = 'ellipse'
                nodes.append({'data': {'id': base64.b16encode(r), 'label': r, 'shape': shape,
                                       'width': len(elm) * 10}})
                if (last_node, elm, r) not in mem_edges:
                    edges.append(
                        {'data': {'id': 'e{}'.format(len(edges)), 'source': base64.b16encode(last_node),
                                  'label': elm + '\n\n',
                                  'target': base64.b16encode(r)}, 'classes': 'end'})
                    mem_edges.add((last_node, elm, r))

    return nodes, edges, list(roots)
