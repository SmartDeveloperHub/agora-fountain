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

from agora.fountain.test import FountainTest


class EmptyVocabTest(FountainTest):
    def test_no_vocabs(self):
        eq_(len(self.get_vocabularies()), False, 'Fountain should be empty')


class CreateAndDeleteSingleVocabTest(FountainTest):
    def test_create_vocab(self):
        vocab_uri = self.post_vocabulary('two_concept_cycle')
        vocabs = self.get_vocabularies()
        eq_(len(vocabs), 1, 'Fountain should contain the simplest cycle vocabulary')
        assert 'twoc' in vocabs, 'The prefix of the contained vocabulary must be "twoc"'
        vocab = self.get_vocabulary(vocab_uri)
        assert len(vocab), 'RDF must not be empty'

    def test_delete_vocab(self):
        self.delete_vocabulary('/vocabs/twoc')
        vocabs = self.get_vocabularies()
        eq_(len(vocabs), False, 'Fountain should be empty again')
        eq_(len(self.types), False, 'There should not be any type available')
        eq_(len(self.properties), False, 'There should not be any property available')
