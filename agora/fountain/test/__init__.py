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

import unittest
from agora.fountain.server import app
from nose.tools import *
import networkx as nx
import json
from functools import wraps


def setup():
    from agora.fountain.server.config import TestingConfig

    app.config['TESTING'] = True
    app.config.from_object(TestingConfig)
    app.config['STORE'] = 'memory'

    from agora.fountain.index.core import r
    r.flushdb()

    from agora.fountain import api


class AgoraGraph(nx.DiGraph):
    def __init__(self, data=None, **attr):
        super(AgoraGraph, self).__init__(data, **attr)

    @property
    def types(self):
        return [t for t, data in self.nodes(data=True) if data['ty'] == 'type']

    @property
    def properties(self):
        return [t for t, data in self.nodes(data=True) if data['ty'] == 'prop']

    def _check_node_type(self, f, ty):
        def wrapper(name):
            for n, data in self.nodes_iter(data=True):
                if n == name:
                    if data['ty'] == ty:
                        return f(name)
                    raise Exception(ty)
            raise KeyError(ty)
        return wrapper

    def get_type_properties(self, ty):
        return self._check_node_type(self.successors, 'type')(ty)

    def get_type_refs(self, ty):
        return self._check_node_type(self.predecessors, 'type')(ty)

    def get_property_domain(self, prop):
        return self._check_node_type(self.predecessors, 'prop')(prop)

    def get_property_range(self, prop):
        return self._check_node_type(self.successors, 'prop')(prop)

    def get_inverse_property(self, prop):
        cycles = list(nx.simple_cycles(self.copy()))
        for cycle in cycles:
            if prop in cycle and len(cycle) == 4:
                p_index = cycle.index(prop)
                return cycle[p_index - 2]
        return None


class FountainTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def tearDown(self):
        pass

    def get(self, path, exp_code=200, error_message=None):
        rv = self.app.get(path)
        if error_message is None:
            error_message = 'There is a problem with the request'
        eq_(rv.status_code, exp_code, error_message)
        return rv.data

    def post(self, path, data, content_type='text/turtle', exp_code=201, message=None):
        rv = self.app.post(path, data=data, headers={'Content-Type': content_type})
        if message is None:
            message = 'The resource was not created properly'
        eq_(rv.status_code, exp_code, message + ": %s" % rv.status_code)
        return rv.data

    def delete(self, path, error_message=None):
        rv = self.app.delete(path)
        if error_message is None:
            error_message = "The resource couldn't be deleted"
        eq_(rv.status_code, 200, error_message)
        return rv.data

    @property
    def types(self):
        return json.loads(self.get('/types'))['types']

    @property
    def properties(self):
        return json.loads(self.get('/properties'))['properties']

    def get_type(self, ty):
        return json.loads(self.get('/types/{}'.format(ty)))

    def get_property(self, ty):
        return json.loads(self.get('/properties/{}'.format(ty)))

    @property
    def graph(self):
        graph = AgoraGraph()
        types = self.types
        graph.add_nodes_from(types, ty='type')
        for node in self.properties:
            p_dict = self.get_property(node)
            dom = p_dict.get('domain')
            ran = p_dict.get('range')
            edges = [(d, node) for d in dom]
            if p_dict.get('type') == 'object':
                edges.extend([(node, r) for r in ran])
            graph.add_edges_from(edges)
            graph.add_node(node, ty='prop', object=p_dict.get('type') == 'object')
        for node in types:
            p_dict = self.get_type(node)
            refs = p_dict.get('refs')
            props = p_dict.get('properties')
            edges = [(r, node) for r in refs]
            edges.extend([(node, p) for p in props])
            graph.add_edges_from(edges)

        return graph


def teardown():
    pass
