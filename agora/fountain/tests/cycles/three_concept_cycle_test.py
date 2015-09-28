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

from agora.fountain.tests import FountainTest
from agora.fountain.tests.util import AgoraGraph, PathGraph, CycleGraph, compare_path_graphs

cycle_0 = CycleGraph()
cycle_0.add_step('test:Concept1', 'test:prop12')
cycle_0.add_step('test:Concept2', 'test:prop23')
cycle_0.add_step('test:Concept3', 'test:prop31')


class ThreeConceptCycleGraphTest(FountainTest):
    def test_graph(self):
        self.post_vocabulary('three_concept_cycle')

        expected_graph = AgoraGraph()
        expected_graph.add_types_from(['test:Concept1', 'test:Concept2', 'test:Concept3'])
        expected_graph.add_properties_from(['test:prop12', 'test:prop23', 'test:prop31'])
        expected_graph.link_types('test:Concept1', 'test:prop12', 'test:Concept2')
        expected_graph.link_types('test:Concept2', 'test:prop23', 'test:Concept3')
        expected_graph.link_types('test:Concept3', 'test:prop31', 'test:Concept1')

        graph = self.graph
        assert graph == expected_graph


seed_uri = "http://localhost/seed"


class ThreeConceptCycleSelfSeedPathsTest(FountainTest):
    def test_self_seed(self):
        self.post_vocabulary('three_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)
        paths, all_cycles = self.get_paths("test:Concept1")

        expected_graph = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': [0]})
        expected_graph.set_cycle(0, cycle_0)

        assert compare_path_graphs([PathGraph(path=path, cycles=all_cycles) for path in paths], [expected_graph])


class ThreeConceptCycleConcept2PathsTest(FountainTest):
    def test_path_concept2(self):
        self.post_vocabulary('three_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)
        paths, all_cycles = self.get_paths('test:Concept2')

        expected_graph = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': [0]})
        expected_graph.add_step('test:Concept1', 'test:prop12')
        expected_graph.set_cycle(0, cycle_0)

        assert compare_path_graphs([PathGraph(path=path, cycles=all_cycles) for path in paths], [expected_graph])


class ThreeConceptCycleConcept3PathsTest(FountainTest):
    def test_path_concept3(self):
        self.post_vocabulary('three_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)
        paths, all_cycles = self.get_paths('test:Concept3')

        expected_graph = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': [0]})
        expected_graph.add_step('test:Concept1', 'test:prop12')
        expected_graph.add_step('test:Concept2', 'test:prop23')
        expected_graph.set_cycle(0, cycle_0)

        assert compare_path_graphs([PathGraph(path=path, cycles=all_cycles) for path in paths], [expected_graph])


class ThreeConceptCyclePartiallySeededPathsTest(FountainTest):
    def test_fully_seeded(self):
        self.post_vocabulary('three_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)
        self.post_seed("test:Concept2", seed_uri + '2')
        paths, all_cycles = self.get_paths('test:Concept3')

        expected_graph_1 = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': [0]})
        expected_graph_1.add_step('test:Concept1', 'test:prop12')
        expected_graph_1.add_step('test:Concept2', 'test:prop23')
        expected_graph_1.set_cycle(0, cycle_0)

        expected_graph_2 = PathGraph(path={'seeds': [seed_uri + '2'], 'steps': [], 'cycles': [0]})
        expected_graph_2.add_step('test:Concept2', 'test:prop23')
        expected_graph_2.set_cycle(0, cycle_0)

        assert compare_path_graphs([PathGraph(path=path, cycles=all_cycles) for path in paths],
                                   [expected_graph_1, expected_graph_2])


class ThreeConceptCycleFullySeededPathsTest(FountainTest):
    def test_fully_seeded(self):
        self.post_vocabulary('three_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)
        self.post_seed("test:Concept2", seed_uri + '2')
        self.post_seed("test:Concept3", seed_uri + '3')
        paths, all_cycles = self.get_paths('test:Concept3')

        expected_graph_1 = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': [0]})
        expected_graph_1.add_step('test:Concept1', 'test:prop12')
        expected_graph_1.add_step('test:Concept2', 'test:prop23')
        expected_graph_1.set_cycle(0, cycle_0)

        expected_graph_2 = PathGraph(path={'seeds': [seed_uri + '2'], 'steps': [], 'cycles': [0]})
        expected_graph_2.add_step('test:Concept2', 'test:prop23')
        expected_graph_2.set_cycle(0, cycle_0)

        expected_graph_3 = PathGraph(path={'seeds': [seed_uri + '3'], 'steps': [], 'cycles': [0]})
        expected_graph_3.set_cycle(0, cycle_0)

        assert compare_path_graphs([PathGraph(path=path, cycles=all_cycles) for path in paths],
                                   [expected_graph_1, expected_graph_2, expected_graph_3])
