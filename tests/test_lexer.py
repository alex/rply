from rply import LexerGenerator


class TestLexer(object):
    def test_simple(self):
        lg = LexerGenerator()
        lg.add("NUMBER", r"\d+")
        lg.add("PLUS", r"\+")

        l = lg.build()

        stream = l.lex("2+3")
        t = next(stream)
        assert t.name == "NUMBER"
        assert t.value == "2"
        t = next(stream)
        assert t.name == "PLUS"
        assert t.value == "+"
        t = next(stream)
        assert t.next == "NUMBER"
        assert t.value == "3"
        assert t.source_pos.idx == 2
        t = next(stream)
        assert t is None
