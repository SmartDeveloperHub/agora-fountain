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


class SeedCRDTest(FountainTest):
    seed_uri = "http://localhost/seed"

    def test_no_seeds(self):
        seeds = self.get_seeds()
        eq_(len(seeds), False, 'There should not be any seed available')

    def test_post_unknown_seed_type(self):
        self.post_seed("test:Concept1", self.seed_uri, exp_code=400)

    def test_post_known_seed_type(self):
        vocab_uri = self.post_vocabulary('simplest_cycle')
        self.post_seed("test:Concept1", self.seed_uri)
        seeds = self.get_seeds()
        assert 'test:Concept1' in seeds, '%s should be the only seed type'
        c1_seeds = seeds['test:Concept1']
        assert len(c1_seeds) == 1 and self.seed_uri in c1_seeds, '%s should be the only seed available' % self.seed_uri
        self.delete_vocabulary(vocab_uri)
        seeds = self.get_seeds()
        eq_(len(seeds), 0, 'No seed should be kept')
