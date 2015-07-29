__author__ = 'fernando'

from agora.fountain.test import FountainTest


class TypesTest(FountainTest):
    def test_get_types(self):
        rv = self.app.get('/types')
        assert rv.status_code == 200

