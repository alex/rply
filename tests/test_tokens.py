from rply.token import Token, SourcePosition


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
