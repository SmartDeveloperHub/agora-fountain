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


class DummyTest(FountainTest):
    def a_test_empty_vocabs(self):
        vocabs = json.loads(self.get('/vocabs'))
        eq_(len(vocabs), False, 'Fountain should be empty')

    def b_test_post_dummy_vocab(self):
        with open('agora/fountain/test/vocabs/dummy.ttl') as f:
            dummy_vocab = f.read()
            self.post('/vocabs', dummy_vocab, message='The vocabulary was not created properly')

    def c_test_contains_dummy(self):
        vocabs = json.loads(self.get('/vocabs'))
        eq_(len(vocabs), 1, 'Fountain should contain the dummy vocab')
        assert 'test' in vocabs, 'The prefix of the contained vocabulary must be "test"'
        vocab = self.get('/vocabs/test')
        assert len(vocab), 'RDF must not be empty'

    def c1_test_dummy_properties(self):
        props = json.loads(self.get('/properties'))["properties"]
        eq_(len(props), 2, 'Fountain should contain two properties, but found: %s' % len(props))
        props = sorted(props)
        assert 'test:prop1' == props.pop(0)
        assert 'test:prop2' == props.pop()

        rv = self.app.get('/properties/test:prop1')
        eq_(rv.status_code, 200, 'test:prop1 is having some problems...')
        rv = self.app.get('/types/test:prop2')
        eq_(rv.status_code, 200, 'test:prop2 is having some problems...')

    def c1_test_dummy_types(self):
        types = json.loads(self.get('/types'))["types"]
        eq_(len(types), 2, 'Fountain should contain two types, but found: %s' % len(types))
        types = sorted(types)
        assert 'test:Concept1' == types.pop(0)
        assert 'test:Concept2' == types.pop()

        rv = self.app.get('/types/test:Concept1')
        eq_(rv.status_code, 200, 'test:Concept1 is having some problems...')
        rv = self.app.get('/types/test:Concept2')
        eq_(rv.status_code, 200, 'test:Concept2 is having some problems...')

    def d_test_delete_dummy_vocab(self):
        self.delete('/vocabs/test', 'The test vocabulary should exist previously')


