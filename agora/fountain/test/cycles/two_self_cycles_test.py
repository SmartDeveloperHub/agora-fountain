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
from agora.fountain.test.util import AgoraGraph, PathGraph, compare_path_graphs


class TwoSelfCyclesGraphTest(FountainTest):
    def test_graph(self):
        self.post_vocabulary('two_self_cycles')

        expected_graph = AgoraGraph()
        expected_graph.add_types_from(['test:Concept1'])
        expected_graph.add_properties_from(['test:prop11a', 'test:prop11b'])
        expected_graph.link_types('test:Concept1', 'test:prop11a', 'test:Concept1')
        expected_graph.link_types('test:Concept1', 'test:prop11b', 'test:Concept1')

        graph = self.graph
        assert graph == expected_graph


seed_uri = "http://localhost/seed"


class TwoSelfCyclesPathsTest(FountainTest):
    def test_path(self):
        self.post_vocabulary('two_self_cycles')
        self.post_seed("test:Concept1", seed_uri)
        paths, all_cycles = self.get_paths("test:Concept1")

        expected_graph = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': [0, 1]},
                                   cycles=[{'cycle': 0, 'steps': []}, {'cycle': 1, 'steps': []}])
        expected_graph.get_cycle(0).add_step('test:Concept1', 'test:prop11a')
        expected_graph.get_cycle(1).add_step('test:Concept1', 'test:prop11b')

        assert compare_path_graphs([PathGraph(path=path, cycles=all_cycles) for path in paths], [expected_graph])
