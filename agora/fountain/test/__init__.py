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
import json
from urlparse import urlparse
import logging

from nose.tools import *

from agora.fountain.server import app
from agora.fountain.test.util import AgoraGraph


def setup():
    from agora.fountain.server.config import TestingConfig

    app.config['TESTING'] = True
    app.config.from_object(TestingConfig)
    app.config['STORE'] = 'memory'

    from agora.fountain.index.core import r
    r.flushdb()

    from agora.fountain import api


class FountainTest(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        from agora.fountain.index.core import r
        r.flushdb()

        test_client = app.test_client()
        vocabs = json.loads(test_client.get('/vocabs').data)
        for v_uri in vocabs.values():
            rv = test_client.delete(v_uri)
            eq_(rv.status_code, 200, "The resource couldn't be deleted")

    @classmethod
    def setUpClass(cls):
        from agora.fountain.index.core import r
        r.flushdb()

    def setUp(self):
        self.app = app.test_client()
        self._graph = None
        self.log = logging.getLogger('agora.fountain.test')

    def get_vocabularies(self):
        return json.loads(self.get('/vocabs'))

    def get_vocabulary(self, uri):
        path = urlparse(uri).path
        return self.get(path)

    def post_vocabulary(self, filename, exp_code=201):
        with open('agora/fountain/test/vocabs/{}.ttl'.format(filename)) as f:
            vocab = f.read()
            response = self.post('/vocabs', vocab, message='The vocabulary was not created properly', exp_code=exp_code)
            if exp_code != 201:
                return None
            return response.headers.get('Location', None)

    def delete_vocabulary(self, uri):
        path = urlparse(uri).path
        self.delete(path, 'The test vocabulary should exist previously')

    def post_seed(self, ty, uri, exp_code=201):
        response = self.post('/seeds', json.dumps({"uri": uri, "type": ty}),
                             content_type='application/json', exp_code=exp_code)

        return response.headers.get('Location', None)

    def delete_seed(self, uri):
        path = urlparse(uri).path
        self.delete(path, 'That seed should exist previously')

    def get_type_seeds(self, ty):
        return json.loads(self.get('/seeds/{}'.format(ty)))["seeds"]

    @property
    def seeds(self):
        return json.loads(self.get('/seeds'))["seeds"]

    def get_paths(self, node):
        paths = json.loads(self.get('paths/{}'.format(node)))
        return paths["paths"], paths["all-cycles"]

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
        return rv

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
        if self._graph is None:
            _graph = AgoraGraph()
            types = self.types
            _graph.add_types_from(types)
            for node in self.properties:
                p_dict = self.get_property(node)
                dom = p_dict.get('domain')
                ran = p_dict.get('range')
                edges = [(d, node) for d in dom]
                if p_dict.get('type') == 'object':
                    edges.extend([(node, r) for r in ran])
                _graph.add_edges_from(edges)
                _graph.add_property(node, obj=p_dict.get('type') == 'object')
            for node in types:
                p_dict = self.get_type(node)
                refs = p_dict.get('refs')
                props = p_dict.get('properties')
                edges = [(r, node) for r in refs]
                edges.extend([(node, p) for p in props])
                _graph.add_edges_from(edges)
                if p_dict['super']:
                    _graph[node]['super'] = p_dict['super']
                if p_dict['sub']:
                    _graph[node]['sub'] = p_dict['sub']

        return _graph

    def check_property(self, name, domain=None, range=None, inverse=None):
        def check_edge(p_name, direction, func, expected):
            actual = func(p_name)
            if type(expected) is list:
                eq_(len(actual), len(expected), '{} must have {} {} type'.format(p_name, len(expected), direction))
                eq_(len(set.difference(set(actual), set(expected))), 0,
                    'Found wrong %s types: %s' % (direction, actual))
            elif len(actual):
                assert 'No %s was expected!' % direction

        check_edge(name, 'domain', self.graph.get_property_domain, domain)
        check_edge(name, 'range', self.graph.get_property_range, range)

        actual_inverse = self.graph.get_inverse_property(name)
        eq_(actual_inverse, inverse, 'Expected {} as inverse, but found: {}'.format(inverse, actual_inverse))

    def check_type(self, name, properties=None, refs=None):
        def check_attribute(p_name, attribute, func, expected):
            actual = func(p_name)
            if type(expected) is list:
                eq_(len(actual), len(expected), '{} must have {} {}'.format(p_name, len(expected), attribute))
                eq_(len(set.difference(set(actual), set(expected))), 0,
                    'Found wrong %s: %s' % (attribute, actual))
            elif len(actual):
                assert 'No %s was expected!' % attribute

        check_attribute(name, 'properties', self.graph.get_type_properties, properties)
        check_attribute(name, 'references', self.graph.get_type_refs, refs)
