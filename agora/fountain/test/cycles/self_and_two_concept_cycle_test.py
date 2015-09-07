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


class SelfAndTwoConceptCycleGraphTest(FountainTest):
    def test_graph(self):
        self.post_vocabulary('two_concept_cycle')
        self.post_vocabulary('self_cycle')
        graph = self.graph
        props = sorted(graph.properties)
        eq_(len(props), 3, 'Fountain should contain three properties, but found: %s' % len(props))
        assert 'test:prop12' in props and 'test:prop21' in props and 'test:prop11a' in props

        # prop12
        p12_domain = graph.get_property_domain('test:prop12')
        eq_(len(p12_domain), 1, 'prop12 must have 1 domain type')
        assert 'test:Concept1' in p12_domain
        p12_range = graph.get_property_range('test:prop12')
        eq_(len(p12_range), 1, 'prop12 must have 1 range type')
        assert 'test:Concept2' in p12_range
        p12_inverse = graph.get_inverse_property('test:prop12')
        eq_(p12_inverse, 'test:prop21', 'test:prop21 is the inverse of test:prop12')

        # prop21
        p21_domain = graph.get_property_domain('test:prop21')
        eq_(len(p21_domain), 1, 'prop21 must have 1 domain type')
        assert 'test:Concept2' in p21_domain
        p21_range = graph.get_property_range('test:prop21')
        eq_(len(p21_range), 1, 'prop21 must have 1 range type')
        assert 'test:Concept1' in p21_range
        p21_inverse = graph.get_inverse_property('test:prop21')
        eq_(p21_inverse, 'test:prop12', 'test:prop12 is the inverse of test:prop21')

        # prop11a
        p11a_domain = graph.get_property_domain('test:prop11a')
        eq_(len(p11a_domain), 1, 'prop11a must have 1 domain type')
        assert 'test:Concept1' in p11a_domain
        p11a_range = graph.get_property_range('test:prop11a')
        eq_(len(p11a_range), 1, 'prop11a must have 1 range type')
        assert 'test:Concept1' in p11a_range
        p11a_inverse = graph.get_inverse_property('test:prop11a')
        eq_(p11a_inverse, None, 'test:prop11a has no inverse')

        types = sorted(graph.types)
        eq_(len(types), 2, 'Fountain should contain two types, but found: %s' % len(types))
        assert 'test:Concept1' == types.pop(0)
        assert 'test:Concept2' == types.pop()

        # Concept 1
        c1_properties = graph.get_type_properties('test:Concept1')
        eq_(len(c1_properties), 2, 'Concept1 must have two properties')
        assert 'test:prop12' in c1_properties and 'test:prop11a' in c1_properties
        c1_refs = graph.get_type_refs('test:Concept1')
        eq_(len(c1_refs), 2, 'Concept1 must have two references')
        assert 'test:prop21' in c1_refs and 'test:prop11a' in c1_refs

        # Concept 2
        c2_properties = graph.get_type_properties('test:Concept2')
        eq_(len(c2_properties), 1, 'Concept2 must have 1 property')
        assert 'test:prop21' in c2_properties
        c2_refs = graph.get_type_refs('test:Concept2')
        eq_(len(c2_refs), 1, 'Concept2 must have 1 reference')
        assert 'test:prop12' in c2_refs


seed_uri = "http://localhost/seed"


class SelfAndTwoConceptCycleSelfSeedPathsTest(FountainTest):
    def test_self_seed(self):
        self.post_vocabulary('two_concept_cycle')
        self.post_vocabulary('self_cycle')
        self.post_seed("test:Concept1", seed_uri)
        c1_paths, all_cycles = self.get_paths("test:Concept1")
        eq_(len(c1_paths), 1, 'Only one path was expected')
        c1_path = c1_paths.pop()
        eq_(len(c1_path['steps']), 0, 'Steps list should be empty')
        eq_(len(c1_path['seeds']), 1, 'test:Concept1 seed was expected')
        c1_path_seed = c1_path['seeds'].pop()
        eq_(c1_path_seed, seed_uri, 'Someone has changed it maliciously...')
        c1_cycles = c1_path['cycles']
        assert len(c1_cycles) == 2 and c1_cycles.pop() == 0, 'test:Concept1 should belong to two cycles'
        eq_(len(all_cycles), 2)


class SelfAndTwoConceptCycleSeedlessConceptPathsTest(FountainTest):
    def test_seedless_concept(self):
        self.post_vocabulary('two_concept_cycle')
        self.post_vocabulary('self_cycle')
        self.post_seed("test:Concept1", seed_uri)
        c2_paths, _ = self.get_paths('test:Concept2')
        eq_(len(c2_paths), 1, 'Only one path was expected')
        c2_path = c2_paths.pop()
        eq_(len(c2_path['steps']), 1, 'Steps list must have length 1')
        eq_(len(c2_path['seeds']), 1, 'test:Concept1 seed was expected')
        c2_path_seed = c2_path['seeds'].pop()
        eq_(c2_path_seed, seed_uri, 'Someone has changed it maliciously...')
        c2_cycles = c2_path['cycles']
        assert len(c2_cycles) == 2, 'There should be two cycles in the resulting path'


class SelfAndTwoConceptCycleFullySeededPathsTest(FountainTest):
    def test_fully_seeded(self):

        def check_seed(s, expected):
            eq_(s, expected, "%s should be the seed for this path" % expected)

        self.post_vocabulary('two_concept_cycle')
        self.post_vocabulary('self_cycle')
        self.post_seed("test:Concept1", seed_uri)
        self.post_seed("test:Concept2", seed_uri + '2')
        c2_paths, _ = self.get_paths('test:Concept2')
        eq_(len(c2_paths), 2, 'Two paths are expected')

        for path in c2_paths:
            steps_len = len(path["steps"])
            seeds = path["seeds"]
            eq_(len(seeds), 1, "Only one seed is expected")
            seed = seeds.pop()
            if steps_len == 1:  # Path with Concept1 seed (candidate)
                check_seed(seed, seed_uri)
            elif steps_len == 0:  # Path with Concept2 seed (candidate)
                check_seed(seed, seed_uri + '2')
            else:
                assert False, 'Invalid path with unexpected number of steps'

            cycles = path['cycles']
            assert len(cycles) == 2, 'There should be two cycles in each resulting path'
