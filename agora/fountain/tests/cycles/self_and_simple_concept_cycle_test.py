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
cycle_0.add_step('test:Concept2', 'test:prop22')


class SelfAndSimpleConceptCycleGraphTest(FountainTest):
    def test_graph(self):
        self.post_vocabulary('simple_two_concepts')
        self.post_vocabulary('self_cycle_2')

        expected_graph = AgoraGraph()
        expected_graph.add_types_from(['test:Concept1', 'test:Concept2'])
        expected_graph.add_properties_from(['test:prop21', 'test:prop22'])
        expected_graph.link_types('test:Concept2', 'test:prop21', 'test:Concept1')
        expected_graph.link_types('test:Concept2', 'test:prop22', 'test:Concept2')

        graph = self.graph
        assert graph == expected_graph


seed_uri = "http://localhost/seed"


class SelfAndSimpleConceptCycleSelfSeedPathsTest(FountainTest):
    def test_self_seed(self):
        self.post_vocabulary('simple_two_concepts')
        self.post_vocabulary('self_cycle_2')
        self.post_seed("test:Concept2", seed_uri)
        c1_paths, all_cycles = self.get_paths("test:Concept2")

        expected_graph = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': [0]})
        expected_graph.set_cycle(0, cycle_0)

        assert compare_path_graphs([PathGraph(path=path, cycles=all_cycles) for path in c1_paths], [expected_graph])


class SelfAndSimpleConceptCycleSeedlessConceptPathsTest(FountainTest):
    def test_seedless_concept(self):
        self.post_vocabulary('simple_two_concepts')
        self.post_vocabulary('self_cycle_2')
        self.post_seed("test:Concept2", seed_uri)
        c1_paths, all_cycles = self.get_paths('test:Concept1')

        expected_graph = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': [0]})
        expected_graph.add_step('test:Concept2', 'test:prop21')
        expected_graph.set_cycle(0, cycle_0)

        assert compare_path_graphs([PathGraph(path=path, cycles=all_cycles) for path in c1_paths], [expected_graph])
