from rply.token import Token, SourcePosition


class TestTokens(object):
    def test_source_pos(self):
        t = Token("VALUE", "3", SourcePosition(5, 2, 1))
        assert t.getsourcepos().lineno == 2
