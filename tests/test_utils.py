from operator import itemgetter

import py

from rply.utils import IdentityDict


class TestIdentityDict(object):
    def test_create(self):
        IdentityDict()

    def test_get_set_item(self):
        d = IdentityDict()
        x = []
        d[x] = "test"
        assert d[x] == "test"

    def test_delitem(self):
        d = IdentityDict()
        x = []
        d[x] = "hello"
        del d[x]
        with py.test.raises(KeyError):
            d[x]

    def test_len(self):
        d = IdentityDict()
        d[[]] = 3
        d[3] = 5
        assert len(d) == 2

    def test_iter(self):
        d = IdentityDict()
        x = []
        y = []

        d[x] = 1
        d[y] = 2

        assert sorted(d.items(), key=itemgetter(1)) == [(x, 1), (y, 2)]
