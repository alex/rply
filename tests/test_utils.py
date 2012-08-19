from operator import itemgetter

from rply.utils import IdentityDict


class TestIdentityDict(object):
    def test_create(self):
        IdentityDict()

    def test_get_set_item(self):
        d = IdentityDict()
        x = []
        d[x] = "test"
        assert d[x] == "test"

    def test_iter(self):
        d = IdentityDict()
        x = []
        y = []

        d[x] = 1
        d[y] = 2

        assert sorted(d.items(), key=itemgetter(1)) == [(x, 1), (y, 2)]
