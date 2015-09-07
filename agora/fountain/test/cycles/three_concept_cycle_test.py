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


class ThreeConceptCycleGraphTest(FountainTest):
    def test_graph(self):
        self.post_vocabulary('three_concept_cycle')
        graph = self.graph
        props = sorted(graph.properties)
        eq_(len(props), 3, 'Fountain should contain three properties, but found: %s' % len(props))
        assert 'test:prop12' in props and 'test:prop23' in props and 'test:prop31' in props

        # prop12
        p12_domain = graph.get_property_domain('test:prop12')
        eq_(len(p12_domain), 1, 'prop12 must have 1 domain type')
        assert 'test:Concept1' in p12_domain
        p12_range = graph.get_property_range('test:prop12')
        eq_(len(p12_range), 1, 'prop12 must have 1 range type')
        assert 'test:Concept2' in p12_range
        p12_inverse = graph.get_inverse_property('test:prop12')
        eq_(p12_inverse, None, 'test:prop12 has no inverse')

        # prop23
        p23_domain = graph.get_property_domain('test:prop23')
        eq_(len(p23_domain), 1, 'prop23 must have 1 domain type')
        assert 'test:Concept2' in p23_domain
        p23_range = graph.get_property_range('test:prop23')
        eq_(len(p23_range), 1, 'prop23 must have 1 range type')
        assert 'test:Concept3' in p23_range
        p23_inverse = graph.get_inverse_property('test:prop23')
        eq_(p23_inverse, None, 'test:prop23 has no inverse')

        # prop31
        p31_domain = graph.get_property_domain('test:prop31')
        eq_(len(p31_domain), 1, 'prop31 must have 1 domain type')
        assert 'test:Concept3' in p31_domain
        p31_range = graph.get_property_range('test:prop31')
        eq_(len(p31_range), 1, 'prop31 must have 1 range type')
        assert 'test:Concept1' in p31_range
        p31_inverse = graph.get_inverse_property('test:prop31')
        eq_(p31_inverse, None, 'test:prop31 has no inverse')

        types = sorted(graph.types)
        eq_(len(types), 3, 'Fountain should contain three types, but found: %s' % len(types))
        assert 'test:Concept1' in types and 'test:Concept2' in types and 'test:Concept3' in types

        # Concept 1
        c1_properties = graph.get_type_properties('test:Concept1')
        eq_(len(c1_properties), 1, 'Concept1 must have 1 property')
        assert 'test:prop12' in c1_properties
        c1_refs = graph.get_type_refs('test:Concept1')
        eq_(len(c1_refs), 1, 'Concept1 must have 1 reference')
        assert 'test:prop31' in c1_refs

        # Concept 2
        c2_properties = graph.get_type_properties('test:Concept2')
        eq_(len(c2_properties), 1, 'Concept2 must have 1 property')
        assert 'test:prop23' in c2_properties
        c2_refs = graph.get_type_refs('test:Concept2')
        eq_(len(c2_refs), 1, 'Concept2 must have 1 reference')
        assert 'test:prop12' in c2_refs

        # Concept 3
        c3_properties = graph.get_type_properties('test:Concept3')
        eq_(len(c3_properties), 1, 'Concept3 must have 1 property')
        assert 'test:prop31' in c3_properties
        c3_refs = graph.get_type_refs('test:Concept3')
        eq_(len(c3_refs), 1, 'Concept2 must have 1 reference')
        assert 'test:prop23' in c3_refs


seed_uri = "http://localhost/seed"


class ThreeConceptCycleSelfSeedPathsTest(FountainTest):
    def test_self_seed(self):
        self.post_vocabulary('three_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)
        c1_paths, all_cycles = self.get_paths("test:Concept1")
        eq_(len(c1_paths), 1, 'Only one path was expected')
        c1_path = c1_paths.pop()
        eq_(len(c1_path['steps']), 0, 'Steps list should be empty')
        eq_(len(c1_path['seeds']), 1, 'test:Concept1 seed was expected')
        c1_path_seed = c1_path['seeds'].pop()
        eq_(c1_path_seed, seed_uri, 'Someone has changed it maliciously...')
        c1_cycles = c1_path['cycles']
        assert len(c1_cycles) == 1 and c1_cycles.pop() == 0, 'test:Concept1 should belong to a cycle'
        eq_(len(all_cycles), 1, "test:Concept1 belongs to an only cycle")
        cycle = all_cycles.pop()
        assert cycle["cycle"] == 0 and len(cycle["steps"]) == 3


class ThreeConceptCycleConcept2PathsTest(FountainTest):
    def test_path_concept2(self):
        self.post_vocabulary('three_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)
        c2_paths, all_cycles = self.get_paths('test:Concept2')
        eq_(len(c2_paths), 1, 'Only one path was expected')
        c2_path = c2_paths.pop()
        eq_(len(c2_path['steps']), 1, 'Steps list must have length 1')
        eq_(len(c2_path['seeds']), 1, 'test:Concept1 seed was expected')
        c2_path_seed = c2_path['seeds'].pop()
        eq_(c2_path_seed, seed_uri, 'Someone has changed it maliciously...')
        c2_cycles = c2_path['cycles']
        assert len(c2_cycles) == 1 and c2_cycles.pop() == 0, 'test:Concept2 should belong to a cycle'
        eq_(len(all_cycles), 1)
        cycle = all_cycles.pop()
        assert cycle["cycle"] == 0 and len(cycle["steps"]) == 3


class ThreeConceptCycleConcept3PathsTest(FountainTest):
    def test_path_concept3(self):
        self.post_vocabulary('three_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)
        c3_paths, all_cycles = self.get_paths('test:Concept3')
        eq_(len(c3_paths), 1, 'Only one path was expected')
        c3_path = c3_paths.pop()
        eq_(len(c3_path['steps']), 2, 'Steps list must have length 2')
        eq_(len(c3_path['seeds']), 1, 'test:Concept1 seed was expected')
        c3_path_seed = c3_path['seeds'].pop()
        eq_(c3_path_seed, seed_uri, 'Someone has changed it maliciously...')
        c3_cycles = c3_path['cycles']
        assert len(c3_cycles) == 1 and c3_cycles.pop() == 0, 'test:Concept3 should belong to a cycle'
        eq_(len(all_cycles), 1)
        cycle = all_cycles.pop()
        assert cycle["cycle"] == 0 and len(cycle["steps"]) == 3


class ThreeConceptCyclePartiallySeededPathsTest(FountainTest):
    def test_fully_seeded(self):
        def check_seed(s, expected):
            eq_(s, expected, "%s should be the seed for this path" % expected)

        self.post_vocabulary('three_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)
        self.post_seed("test:Concept2", seed_uri + '2')
        c3_paths, _ = self.get_paths('test:Concept3')
        eq_(len(c3_paths), 2, 'Two paths are expected')

        for path in c3_paths:
            steps_len = len(path["steps"])
            seeds = path["seeds"]
            eq_(len(seeds), 1, "Only one seed is expected")
            seed = seeds.pop()
            if steps_len == 2:  # Path with Concept1 seed (candidate)
                check_seed(seed, seed_uri)
            elif steps_len == 1:  # Path with Concept2 seed (candidate)
                check_seed(seed, seed_uri + '2')
            else:
                assert False, 'Invalid path with unexpected number of steps'

            cycles = path['cycles']
            assert len(cycles) == 1 and cycles.pop() == 0, 'test:Concept3 should belong to a cycle'


class ThreeConceptCycleFullySeededPathsTest(FountainTest):
    def test_fully_seeded(self):
        def check_seed(s, expected):
            eq_(s, expected, "%s should be the seed for this path" % expected)

        self.post_vocabulary('three_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)
        self.post_seed("test:Concept2", seed_uri + '2')
        self.post_seed("test:Concept3", seed_uri + '3')
        c3_paths, _ = self.get_paths('test:Concept3')
        eq_(len(c3_paths), 3, 'Three paths are expected')

        for path in c3_paths:
            steps_len = len(path["steps"])
            seeds = path["seeds"]
            eq_(len(seeds), 1, "Only one seed is expected")
            seed = seeds.pop()
            if steps_len == 2:  # Path with Concept1 seed (candidate)
                check_seed(seed, seed_uri)
            elif steps_len == 1:  # Path with Concept2 seed (candidate)
                check_seed(seed, seed_uri + '2')
            elif steps_len == 0:  # Path with Concept3 seed (candidate)
                check_seed(seed, seed_uri + '3')
            else:
                assert False, 'Invalid path with unexpected number of steps'

            cycles = path['cycles']
            assert len(cycles) == 1 and cycles.pop() == 0, 'test:Concept3 should belong to a cycle'
