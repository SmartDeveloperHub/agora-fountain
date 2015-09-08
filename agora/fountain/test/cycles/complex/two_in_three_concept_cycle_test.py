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
from nose.tools import *
from agora.fountain.test import AgoraGraph, PathGraph, CycleGraph, compare_path_graphs

cycle_0 = CycleGraph()
cycle_0.add_step('test:Concept1', 'test:prop12')
cycle_0.add_step('test:Concept2', 'test:prop21')
cycle_1 = CycleGraph()
cycle_1.add_step('test:Concept1', 'test:prop12')
cycle_1.add_step('test:Concept2', 'test:prop23')
cycle_1.add_step('test:Concept3', 'test:prop31')


class TwoInThreeConceptCycleGraphTest(FountainTest):
    def test_graph(self):
        self.post_vocabulary('three_concept_cycle')
        self.post_vocabulary('two_concept_cycle')

        expected_graph = AgoraGraph()
        expected_graph.add_node('test:Concept1')
        expected_graph.add_node('test:Concept2')
        expected_graph.add_node('test:Concept3')

        graph = self.graph
        props = sorted(graph.properties)
        eq_(len(props), 4, 'Fountain should contain four properties, but found: %s' % len(props))
        assert 'test:prop12' in props and 'test:prop23' in props and 'test:prop31' in props and 'test:prop21' in props

        self.check_property('test:prop12', domain=['test:Concept1'], range=['test:Concept2'], inverse='test:prop21')
        self.check_property('test:prop21', domain=['test:Concept2'], range=['test:Concept1'], inverse='test:prop12')
        self.check_property('test:prop23', domain=['test:Concept2'], range=['test:Concept3'])
        self.check_property('test:prop31', domain=['test:Concept3'], range=['test:Concept1'])

        types = sorted(graph.types)
        eq_(len(types), 3, 'Fountain should contain three types, but found: %s' % len(types))
        assert 'test:Concept1' in types and 'test:Concept2' in types and 'test:Concept3' in types

        self.check_type('test:Concept1', properties=['test:prop12'], refs=['test:prop31', 'test:prop21'])
        self.check_type('test:Concept2', properties=['test:prop21', 'test:prop23'], refs=['test:prop12'])
        self.check_type('test:Concept3', properties=['test:prop31'], refs=['test:prop23'])


seed_uri = "http://localhost/seed"


class TwoInThreeConceptCycleSelfSeedPathsTest(FountainTest):
    def test_self_seed(self):
        self.post_vocabulary('three_concept_cycle')
        self.post_vocabulary('two_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)

        c1_paths, all_cycles = self.get_paths("test:Concept1")
        eq_(len(c1_paths), 1, 'Only one path was expected')
        c1_path = c1_paths.pop()

        path_graph = PathGraph(path=c1_path, cycles=all_cycles)

        expected_graph = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': [0, 1]})
        expected_graph.set_cycle(0, cycle_0)
        expected_graph.set_cycle(1, cycle_1)

        eq_(path_graph, expected_graph)


class TwoInThreeConceptCycleConcept2PathsTest(FountainTest):
    def test_path_concept2(self):
        self.post_vocabulary('three_concept_cycle')
        self.post_vocabulary('two_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)
        c2_paths, all_cycles = self.get_paths('test:Concept2')
        eq_(len(c2_paths), 1, 'Only one path was expected')
        c2_path = c2_paths.pop()

        path_graph = PathGraph(path=c2_path, cycles=all_cycles)
        expected_graph = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': [0, 1]})

        expected_graph.add_step('test:Concept1', 'test:prop12')
        expected_graph.set_cycle(0, cycle_0)
        expected_graph.set_cycle(1, cycle_1)

        eq_(path_graph, expected_graph)


class TwoInThreeConceptCycleConcept3PathsTest(FountainTest):
    def test_path_concept3(self):
        self.post_vocabulary('three_concept_cycle')
        self.post_vocabulary('two_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)
        c3_paths, all_cycles = self.get_paths('test:Concept3')
        eq_(len(c3_paths), 1, 'Only one path was expected')
        c3_path = c3_paths.pop()

        path_graph = PathGraph(path=c3_path, cycles=all_cycles)
        expected_graph = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': [0, 1]})

        expected_graph.add_step('test:Concept1', 'test:prop12')
        expected_graph.add_step('test:Concept2', 'test:prop23')
        expected_graph.set_cycle(0, cycle_0)
        expected_graph.set_cycle(1, cycle_1)

        eq_(path_graph, expected_graph)


class TwoInThreeConceptCyclePartiallySeededPathsTest(FountainTest):
    def test_fully_seeded(self):
        self.post_vocabulary('three_concept_cycle')
        self.post_vocabulary('two_concept_cycle')
        self.post_seed("test:Concept3", seed_uri + '3')
        self.post_seed("test:Concept2", seed_uri + '2')
        c1_paths, all_cycles = self.get_paths('test:Concept1')

        expected_graph_2a = PathGraph(path={'seeds': [seed_uri + '2'], 'steps': [], 'cycles': [0, 1]})
        expected_graph_2a.add_step('test:Concept2', 'test:prop21')
        expected_graph_2a.set_cycle(0, cycle_0)
        expected_graph_2a.set_cycle(1, cycle_1)

        expected_graph_2b = PathGraph(path={'seeds': [seed_uri + '2'], 'steps': [], 'cycles': [0, 1]})
        expected_graph_2b.add_step('test:Concept2', 'test:prop23')
        expected_graph_2b.add_step('test:Concept3', 'test:prop31')
        expected_graph_2b.set_cycle(0, cycle_0)
        expected_graph_2b.set_cycle(1, cycle_1)

        expected_graph_3 = PathGraph(path={'seeds': [seed_uri + '3'], 'steps': [], 'cycles': [0, 1]})
        expected_graph_3.add_step('test:Concept3', 'test:prop31')
        expected_graph_3.set_cycle(0, cycle_0)
        expected_graph_3.set_cycle(1, cycle_1)

        expected_graphs = [expected_graph_2a, expected_graph_2b, expected_graph_3]

        assert compare_path_graphs([PathGraph(path=path, cycles=all_cycles) for path in c1_paths], expected_graphs)


class TwoInThreeConceptCycleFullySeededPathsTest(FountainTest):
    def test_fully_seeded(self):
        self.post_vocabulary('three_concept_cycle')
        self.post_vocabulary('two_concept_cycle')
        self.post_seed("test:Concept3", seed_uri + '3')
        self.post_seed("test:Concept2", seed_uri + '2')
        self.post_seed("test:Concept1", seed_uri)
        c1_paths, all_cycles = self.get_paths('test:Concept1')

        expected_graph_1 = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': [0, 1]})
        expected_graph_1.set_cycle(0, cycle_0)
        expected_graph_1.set_cycle(1, cycle_1)

        expected_graph_2a = PathGraph(path={'seeds': [seed_uri + '2'], 'steps': [], 'cycles': [0, 1]})
        expected_graph_2a.add_step('test:Concept2', 'test:prop21')
        expected_graph_2a.set_cycle(0, cycle_0)
        expected_graph_2a.set_cycle(1, cycle_1)

        expected_graph_2b = PathGraph(path={'seeds': [seed_uri + '2'], 'steps': [], 'cycles': [0, 1]})
        expected_graph_2b.add_step('test:Concept2', 'test:prop23')
        expected_graph_2b.add_step('test:Concept3', 'test:prop31')
        expected_graph_2b.set_cycle(0, cycle_0)
        expected_graph_2b.set_cycle(1, cycle_1)

        expected_graph_3 = PathGraph(path={'seeds': [seed_uri + '3'], 'steps': [], 'cycles': [0, 1]})
        expected_graph_3.add_step('test:Concept3', 'test:prop31')
        expected_graph_3.set_cycle(0, cycle_0)
        expected_graph_3.set_cycle(1, cycle_1)

        expected_graphs = [expected_graph_1, expected_graph_2a, expected_graph_2b, expected_graph_3]

        assert compare_path_graphs([PathGraph(path=path, cycles=all_cycles) for path in c1_paths], expected_graphs)
