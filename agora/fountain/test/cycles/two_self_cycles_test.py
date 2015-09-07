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

from agora.fountain.test import FountainTest
import json
from nose.tools import *


class TwoSelfCyclesGraphTest(FountainTest):
    def test_graph(self):
        self.post_vocabulary('two_self_cycles')
        graph = self.graph
        props = sorted(graph.properties)
        eq_(len(props), 2, 'Fountain should contain two properties, but found: %s' % len(props))
        assert 'test:prop11a' == props.pop(0)
        assert 'test:prop11b' == props.pop()

        # prop11a
        p11a_domain = graph.get_property_domain('test:prop11a')
        eq_(len(p11a_domain), 1, 'prop11a must have 1 domain type')
        assert 'test:Concept1' in p11a_domain
        p11a_range = graph.get_property_range('test:prop11a')
        eq_(len(p11a_range), 1, 'prop11a must have 1 range type')
        assert 'test:Concept1' in p11a_range
        p11a_inverse = graph.get_inverse_property('test:prop11a')
        eq_(p11a_inverse, None, 'test:prop11a has no inverse')

        # prop11b
        p11b_domain = graph.get_property_domain('test:prop11b')
        eq_(len(p11b_domain), 1, 'prop11b must have 1 domain type')
        assert 'test:Concept1' in p11b_domain
        p11b_range = graph.get_property_range('test:prop11b')
        eq_(len(p11b_range), 1, 'prop11b must have 1 range type')
        assert 'test:Concept1' in p11b_range
        p11b_inverse = graph.get_inverse_property('test:prop11b')
        eq_(p11b_inverse, None, 'test:prop11b has no inverse')

        types = sorted(graph.types)
        eq_(len(types), 1, 'Fountain should contain only one type, but found: %s' % len(types))
        assert 'test:Concept1' == types.pop()

        # Concept 1
        c1_properties = graph.get_type_properties('test:Concept1')
        eq_(len(c1_properties), 2, 'Concept1 must have 2 properties')
        assert 'test:prop11a' in c1_properties and 'test:prop11b' in c1_properties
        c1_refs = graph.get_type_refs('test:Concept1')
        eq_(len(c1_refs), 2, 'Concept1 must have 2 references')
        assert 'test:prop11a' in c1_refs and 'test:prop11b' in c1_refs


seed_uri = "http://localhost/seed"


class TwoSelfCyclesPathsTest(FountainTest):
    def test_path(self):
        self.post_vocabulary('two_self_cycles')
        self.post_seed("test:Concept1", seed_uri)
        c1_paths, _ = self.get_paths("test:Concept1")
        eq_(len(c1_paths), 1, 'Only one path was expected')
        c1_path = c1_paths.pop()
        eq_(len(c1_path['steps']), 0, 'Steps list should be empty')
        eq_(len(c1_path['seeds']), 1, 'test:Concept1 seed was expected')
        c1_path_seed = c1_path['seeds'].pop()
        eq_(c1_path_seed, seed_uri, 'Someone has changed it maliciously...')
        c1_cycles = c1_path['cycles']
        assert len(c1_cycles) == 2, 'test:Concept1 should belong to two cycles'
