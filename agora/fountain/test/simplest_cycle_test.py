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


class SimplestCycleGraphTest(FountainTest):
    def test_properties(self):
        self.post_vocabulary('simplest_cycle')
        graph = self.graph
        props = sorted(graph.properties)
        eq_(len(props), 2, 'Fountain should contain two properties, but found: %s' % len(props))
        assert 'test:prop1' == props.pop(0)
        assert 'test:prop2' == props.pop()

        # prop1
        p1_domain = graph.get_property_domain('test:prop1')
        eq_(len(p1_domain), 1, 'prop1 must have 1 domain type')
        assert 'test:Concept1' in p1_domain
        p1_range = graph.get_property_range('test:prop1')
        eq_(len(p1_range), 1, 'prop1 must have 1 range type')
        assert 'test:Concept2' in p1_range
        p1_inverse = graph.get_inverse_property('test:prop1')
        eq_(p1_inverse, 'test:prop2', 'test:prop2 is the inverse of test:prop1')

        # prop2
        p2_domain = graph.get_property_domain('test:prop2')
        eq_(len(p2_domain), 1, 'prop2 must have 1 domain type')
        assert 'test:Concept2' in p2_domain
        p2_range = graph.get_property_range('test:prop2')
        eq_(len(p2_range), 1, 'prop2 must have 1 range type')
        assert 'test:Concept1' in p2_range
        p2_inverse = graph.get_inverse_property('test:prop2')
        eq_(p2_inverse, 'test:prop1', 'test:prop1 is the inverse of test:prop2')

    def test_types(self):
        graph = self.graph
        types = sorted(graph.types)
        eq_(len(types), 2, 'Fountain should contain two types, but found: %s' % len(types))
        assert 'test:Concept1' == types.pop(0)
        assert 'test:Concept2' == types.pop()

        # Concept 1
        c1_properties = graph.get_type_properties('test:Concept1')
        eq_(len(c1_properties), 1, 'Concept1 must have 1 property')
        assert 'test:prop1' in c1_properties
        c1_refs = graph.get_type_refs('test:Concept1')
        eq_(len(c1_refs), 1, 'Concept1 must have 1 reference')
        assert 'test:prop2' in c1_refs

        # Concept 2
        c2_properties = graph.get_type_properties('test:Concept2')
        eq_(len(c2_properties), 1, 'Concept2 must have 1 property')
        assert 'test:prop2' in c2_properties
        c2_refs = graph.get_type_refs('test:Concept2')
        eq_(len(c2_refs), 1, 'Concept2 must have 1 reference')
        assert 'test:prop1' in c2_refs


class SimplestCyclePathsTest(FountainTest):
    seed_uri = "http://localhost/seed"

    def a_test_seedless_paths(self):
        self.post_vocabulary('simplest_cycle')
        seeds = self.get_seeds()
        eq_(len(seeds), False, 'There should not be any seed available')
        c1_paths = self.get_paths("test:Concept1")
        eq_(len(c1_paths), False, 'Impossible...No seeds, no paths')

    def b_test_path_with_self_seed(self):
        self.post_seed("test:Concept1", self.seed_uri)
        c1_paths = self.get_paths("test:Concept1")
        eq_(len(c1_paths), 1, 'Only one path was expected')
        c1_path = c1_paths.pop()
        eq_(len(c1_path['steps']), 0, 'Steps list should be empty')
        eq_(len(c1_path['seeds']), 1, 'test:Concept1 seed was expected')
        c1_path_seed = c1_path['seeds'].pop()
        eq_(c1_path_seed, self.seed_uri, 'Someone has changed it maliciously...')
        c1_cycles = c1_path['cycles']
        eq_(len(c1_cycles), 1, 'test:Concept1 should belong to a cycle')
        eq_(c1_cycles.pop(), 0, 'test:Concept1 should belong to the cycle 0')

    def c_test_path_to_seedless_concept(self):
        c2_paths = self.get_paths('test:Concept2')
        eq_(len(c2_paths), 1, 'Only one path was expected')
        c2_path = c2_paths.pop()
        eq_(len(c2_path['steps']), 1, 'Steps list must have length 1')
        eq_(len(c2_path['seeds']), 1, 'test:Concept1 seed was expected')
        c2_path_seed = c2_path['seeds'].pop()
        eq_(c2_path_seed, self.seed_uri, 'Someone has changed it maliciously...')
        c2_cycles = c2_path['cycles']
        eq_(len(c2_cycles), 1, 'test:Concept2 should belong to a cycle')
        eq_(c2_cycles.pop(), 0, 'test:Concept2 should belong to the cycle 0')

