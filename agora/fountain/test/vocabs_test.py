__author__ = 'fernando'

from agora.fountain.test import FountainTest
import json
from nose.tools import *


class VocabsTest(FountainTest):
    def a_test_empty_vocabs(self):
        rv = self.app.get('/vocabs')
        eq_(rv.status_code, 200, 'There is a problem with the request')
        vocabs = json.loads(rv.data)
        eq_(len(vocabs), False, 'Fountain should be empty')

    def b_test_post_dummy_vocab(self):
        with open('vocabs/dummy.ttl') as f:
            dummy_vocab = f.read()
            rv = self.app.post('/vocabs', data=dummy_vocab, headers={'Content-Type': 'text/turtle'})
            eq_(rv.status_code, 201, 'The vocabulary was not created properly')

        rv = self.app.get('/vocabs/test')
        assert len(rv.data)

    def c_test_delete_dummy_vocab(self):
        rv = self.app.delete('/vocabs/test')
        eq_(rv.status_code, 200, 'The test vocabulary should exist previously')


