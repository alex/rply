from rply.token import SourcePosition, Token


class TestTokens(object):
    def test_source_pos(self):
        t = Token("VALUE", "3", SourcePosition(5, 2, 1))
        assert t.getsourcepos().lineno == 2

    def test_eq(self):
        t = Token("VALUE", "3", SourcePosition(-1, -1, -1))
        assert not (t == 3)
        assert t != 3

    def test_repr(self):
        t = Token("VALUE", "3")
        assert repr(t) == "Token('VALUE', '3')"


class TestSourcePosition(object):
    def test_source_pos(self):
        sp = SourcePosition(1, 2, 3)
        assert sp.idx == 1
        assert sp.lineno == 2
        assert sp.colno == 3

    def test_repr(self):
        t = SourcePosition(1, 2, 3)
        assert repr(t) == "SourcePosition(idx=1, lineno=2, colno=3)"
