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


class SelfAndSimpleConceptCycleGraphTest(FountainTest):
    def test_graph(self):
        self.post_vocabulary('simple_two_concepts')
        self.post_vocabulary('self_cycle_2')
        graph = self.graph
        props = sorted(graph.properties)
        eq_(len(props), 2, 'Fountain should contain two properties, but found: %s' % len(props))
        assert 'test:prop21' in props and 'test:prop22' in props

        # prop22
        p22_domain = graph.get_property_domain('test:prop22')
        eq_(len(p22_domain), 1, 'prop22 must have 1 domain type')
        assert 'test:Concept2' in p22_domain
        p22_range = graph.get_property_range('test:prop22')
        eq_(len(p22_range), 1, 'prop22 must have 1 range type')
        assert 'test:Concept2' in p22_range
        p22_inverse = graph.get_inverse_property('test:prop22')
        eq_(p22_inverse, None, 'test:prop22 has no inverse')

        types = sorted(graph.types)
        eq_(len(types), 2, 'Fountain should contain two types, but found: %s' % len(types))
        assert 'test:Concept1' in types and 'test:Concept2' in types

        # Concept 1
        c1_properties = graph.get_type_properties('test:Concept1')
        eq_(len(c1_properties), 0, 'Concept1 must have no properties')
        c1_refs = graph.get_type_refs('test:Concept1')
        eq_(len(c1_refs), 1, 'Concept1 must have only one reference')
        assert 'test:prop21' in c1_refs

        # Concept 2
        c2_properties = graph.get_type_properties('test:Concept2')
        eq_(len(c2_properties), 2, 'Concept2 must have 2 properties')
        assert 'test:prop21' in c2_properties and 'test:prop22' in c2_properties
        c2_refs = graph.get_type_refs('test:Concept2')
        eq_(len(c2_refs), 1, 'Concept2 must have 1 reference')
        assert 'test:prop22' in c2_refs


seed_uri = "http://localhost/seed"


class SelfAndSimpleConceptCycleSelfSeedPathsTest(FountainTest):
    def test_self_seed(self):
        self.post_vocabulary('simple_two_concepts')
        self.post_vocabulary('self_cycle_2')
        self.post_seed("test:Concept2", seed_uri)
        c1_paths, all_cycles = self.get_paths("test:Concept2")
        eq_(len(c1_paths), 1, 'Only one path was expected')
        c1_path = c1_paths.pop()
        eq_(len(c1_path['steps']), 0, 'Steps list should be empty')
        eq_(len(c1_path['seeds']), 1, 'test:Concept1 seed was expected')
        c1_path_seed = c1_path['seeds'].pop()
        eq_(c1_path_seed, seed_uri, 'Someone has changed it maliciously...')
        c1_cycles = c1_path['cycles']
        assert len(c1_cycles) == 1, 'The path contains only one cycle'
        eq_(len(all_cycles), 1)


class SelfAndSimpleConceptCycleSeedlessConceptPathsTest(FountainTest):
    def test_seedless_concept(self):
        self.post_vocabulary('simple_two_concepts')
        self.post_vocabulary('self_cycle_2')
        self.post_seed("test:Concept2", seed_uri)
        c1_paths, _ = self.get_paths('test:Concept1')
        eq_(len(c1_paths), 1, 'Only one path was expected')
        c1_path = c1_paths.pop()
        eq_(len(c1_path['steps']), 1, 'Steps list must have length 1')
        eq_(len(c1_path['seeds']), 1, 'test:Concept1 seed was expected')
        c1_path_seed = c1_path['seeds'].pop()
        eq_(c1_path_seed, seed_uri, 'Someone has changed it maliciously...')
        c1_cycles = c1_path['cycles']
        assert len(c1_cycles) == 1, 'The path should contain one cycle'
