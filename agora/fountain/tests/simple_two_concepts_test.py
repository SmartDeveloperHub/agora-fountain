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

from nose.tools import *

from agora.fountain.tests import FountainTest
from agora.fountain.tests.util import AgoraGraph, PathGraph, compare_path_graphs


class SimpleTwoConceptsGraphTest(FountainTest):
    def test_graph(self):
        self.post_vocabulary('simple_two_concepts')

        expected_graph = AgoraGraph()
        expected_graph.add_types_from(['test:Concept1', 'test:Concept2'])
        expected_graph.add_properties_from(['test:prop21'])
        expected_graph.link_types('test:Concept2', 'test:prop21', 'test:Concept1')

        graph = self.graph
        assert graph == expected_graph


seed_uri = "http://localhost/seed"


class SimpleTwoConceptsPropertyPathTest(FountainTest):
    def a_test_self_seed(self):
        self.post_vocabulary('simple_two_concepts')
        self.post_seed("test:Concept2", seed_uri)
        paths, all_cycles = self.get_paths("test:prop21")

        expected_graph = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': []})
        expected_graph.add_step('test:Concept2', 'test:prop21')

        assert compare_path_graphs([PathGraph(path=path, cycles=all_cycles) for path in paths], [expected_graph])


class SimpleTwoConceptsSelfSeedPathsTest(FountainTest):
    def a_test_self_seed(self):
        self.post_vocabulary('simple_two_concepts')
        self.post_seed("test:Concept1", seed_uri)
        paths, all_cycles = self.get_paths("test:Concept1")

        expected_graph = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': []})

        assert compare_path_graphs([PathGraph(path=path, cycles=all_cycles) for path in paths], [expected_graph])

    def b_test_no_path(self):
        c1_paths, _ = self.get_paths("test:Concept2")
        eq_(len(c1_paths), 0, 'No path was expected')


class SimpleTwoConceptsSeedlessPathsTest(FountainTest):
    def test_seedless_concept(self):
        self.post_vocabulary('simple_two_concepts')
        self.post_seed("test:Concept2", seed_uri)
        paths, all_cycles = self.get_paths("test:Concept1")

        expected_graph = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': []})
        expected_graph.add_step('test:Concept2', 'test:prop21')

        assert compare_path_graphs([PathGraph(path=path, cycles=all_cycles) for path in paths], [expected_graph])


class SimpleTwoConceptsFullySeededPathsTest(FountainTest):
    def test_fully_seeded(self):
        self.post_vocabulary('simple_two_concepts')
        self.post_seed("test:Concept1", seed_uri)
        self.post_seed("test:Concept2", seed_uri + '2')
        paths, all_cycles = self.get_paths("test:Concept1")

        expected_graph_1 = PathGraph(path={'seeds': [seed_uri], 'steps': [], 'cycles': []})

        expected_graph_2 = PathGraph(path={'seeds': [seed_uri + '2'], 'steps': [], 'cycles': []})
        expected_graph_2.add_step('test:Concept2', 'test:prop21')

        assert compare_path_graphs([PathGraph(path=path, cycles=all_cycles) for path in paths],
                                   [expected_graph_1, expected_graph_2])
