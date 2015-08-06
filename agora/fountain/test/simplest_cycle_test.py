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
        graph = self.graph
        props = sorted(graph.properties)
        eq_(len(props), 2, 'Fountain should contain two properties, but found: %s' % len(props))
        assert 'test:prop1' == props.pop(0)
        assert 'test:prop2' == props.pop()

        # prop1
        p1_domain = graph.get_property_domain('test:prop1')
        eq_(len(p1_domain), 1, 'prop1 must have 1 domain type')
        assert 'test:Concept1' in p1_domain
        p1_range = graph.get_property_range('test:prop1')
        eq_(len(p1_range), 1, 'prop1 must have 1 range type')
        assert 'test:Concept2' in p1_range
        p1_inverse = graph.get_inverse_property('test:prop1')
        eq_(p1_inverse, 'test:prop2', 'test:prop2 is the inverse of test:prop1')

        # prop2
        p2_domain = graph.get_property_domain('test:prop2')
        eq_(len(p2_domain), 1, 'prop2 must have 1 domain type')
        assert 'test:Concept2' in p2_domain
        p2_range = graph.get_property_range('test:prop2')
        eq_(len(p2_range), 1, 'prop2 must have 1 range type')
        assert 'test:Concept1' in p2_range
        p2_inverse = graph.get_inverse_property('test:prop2')
        eq_(p2_inverse, 'test:prop1', 'test:prop1 is the inverse of test:prop2')

    def c1_test_dummy_types(self):
        graph = self.graph
        types = sorted(graph.types)
        eq_(len(types), 2, 'Fountain should contain two types, but found: %s' % len(types))
        assert 'test:Concept1' == types.pop(0)
        assert 'test:Concept2' == types.pop()

        # Concept 1
        c1_properties = graph.get_type_properties('test:Concept1')
        eq_(len(c1_properties), 1, 'Concept1 must have 1 property')
        assert 'test:prop1' in c1_properties
        c1_refs = graph.get_type_refs('test:Concept1')
        eq_(len(c1_refs), 1, 'Concept1 must have 1 reference')
        assert 'test:prop2' in c1_refs

        # Concept 2
        c2_properties = graph.get_type_properties('test:Concept2')
        eq_(len(c2_properties), 1, 'Concept2 must have 1 property')
        assert 'test:prop2' in c2_properties
        c2_refs = graph.get_type_refs('test:Concept2')
        eq_(len(c2_refs), 1, 'Concept2 must have 1 reference')
        assert 'test:prop1' in c2_refs

    def d_test_delete_dummy_vocab(self):
        self.delete('/vocabs/test', 'The test vocabulary should exist previously')
