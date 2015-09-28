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

seed_uri = "http://localhost/seed"


class UnknownSeedTest(FountainTest):
    def test_unknown_seed(self):
        seeds = self.seeds
        eq_(len(seeds), False, 'There should not be any seed available')
        self.post_seed("test:Concept1", seed_uri, exp_code=400)


class KnownSeedTest(FountainTest):
    def test_known_seed(self):
        self.post_vocabulary('two_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)
        seeds = self.seeds
        assert 'test:Concept1' in seeds, '%s should be the only seed type'
        c1_seeds = seeds['test:Concept1']
        assert len(c1_seeds) == 1 and seed_uri in c1_seeds, '%s should be the only seed available' % seed_uri


class DuplicateSeedTest(FountainTest):
    def test_duplicate_seed(self):
        self.post_vocabulary('two_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)
        self.post_seed("test:Concept1", seed_uri, exp_code=409)


class ClearSeedTest(FountainTest):
    def test_clear_seed(self):
        self.post_vocabulary('two_concept_cycle')
        self.post_seed("test:Concept1", seed_uri)
        vocabs = self.get_vocabularies()
        self.delete_vocabulary(vocabs[vocabs.keys().pop()])  # It assumes it contains only one
        seeds = self.seeds
        eq_(len(seeds), 0, 'No seed should be kept')


class TwoTypesSeedTest(FountainTest):
    def test_two_types_seeds(self):
        c1 = "test:Concept1"
        c2 = "test:Concept2"
        self.post_vocabulary('two_concept_cycle')
        self.post_seed(c1, seed_uri)
        self.post_seed(c2, seed_uri + '2')
        seeds = self.seeds
        assert c1 in seeds and c2 in seeds, '%s and %s should be the two seed types' % (c1, c2)
        c1_seeds = seeds['test:Concept1']
        assert len(c1_seeds) == 1 and seed_uri in c1_seeds, '%s should be the only seed available of type %s' % (
            seed_uri, c1)
        c2_seeds = seeds['test:Concept2']
        assert len(c2_seeds) == 1 and seed_uri + '2' in c2_seeds, '%s should be the only seed available of type %s' % (
            seed_uri, c2)


class MultipleSeedsOfSameTypeTest(FountainTest):
    def test_multiple_seeds(self):
        c1 = "test:Concept1"
        self.post_vocabulary('two_concept_cycle')
        self.post_seed(c1, seed_uri)
        self.post_seed(c1, seed_uri + '2')
        seeds = self.seeds
        assert c1 in seeds, '%s should be the only seed type' % c1
        c1_seeds = seeds[c1]
        assert len(
            c1_seeds) == 2 and seed_uri in c1_seeds and seed_uri + '2' in c1_seeds, \
            '%s and %s should be the only seeds available of type %s' % (
                seed_uri, seed_uri + '2', c1)


class SeedsByTypeTest(FountainTest):
    def test_type_seeds(self):
        c1 = "test:Concept1"
        self.post_vocabulary('two_concept_cycle')
        self.post_seed(c1, seed_uri)
        c1_seeds = self.get_type_seeds(c1)
        assert len(c1_seeds) == 1 and seed_uri in c1_seeds, '%s should be the only seed available of type %s' % (
            seed_uri, c1)


class SeedsByUnknownTypeTest(FountainTest):
    def test_type_seeds(self):
        c1 = "test:Concept2"
        self.post_vocabulary('two_concept_cycle')
        self.post_seed(c1, seed_uri)
        try:
            self.get_type_seeds('unknown')
            assert False
        except AssertionError:
            pass
