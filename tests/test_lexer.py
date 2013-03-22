from pytest import raises

from rply import LexerGenerator


class TestLexer(object):
    def test_simple(self):
        lg = LexerGenerator()
        lg.add("NUMBER", r"\d+")
        lg.add("PLUS", r"\+")

        l = lg.build()

        stream = l.lex("2+3")
        t = stream.next()
        assert t.name == "NUMBER"
        assert t.value == "2"
        t = stream.next()
        assert t.name == "PLUS"
        assert t.value == "+"
        t = stream.next()
        assert t.name == "NUMBER"
        assert t.value == "3"
        assert t.source_pos.idx == 2
        t = stream.next()
        assert t is None

    def test_simple_iter(self):
        lg = LexerGenerator()
        lg.add("NUMBER", r"\d+")
        lg.add("PLUS", r"\+")

        l = lg.build()

        iterator = iter(l.lex("2+3"))
        t = iterator.next()
        assert t.name == "NUMBER"
        assert t.value == "2"
        t = iterator.next()
        assert t.name == "PLUS"
        assert t.value == "+"
        t = iterator.next()
        assert t.name == "NUMBER"
        assert t.value == "3"
        assert t.source_pos.idx == 2

        with raises(StopIteration):
            t = iterator.next()

    def test_ignore(self):
        lg = LexerGenerator()
        lg.add("NUMBER", r"\d+")
        lg.add("PLUS", r"\+")
        lg.ignore(r"\s+")

        l = lg.build()

        stream = l.lex("2 + 3")
        t = stream.next()
        assert t.name == "NUMBER"
        assert t.value == "2"
        t = stream.next()
        assert t.name == "PLUS"
        assert t.value == "+"
        t = stream.next()
        assert t.name == "NUMBER"
        assert t.value == "3"
        assert t.source_pos.idx == 4
        t = stream.next()
        assert t is None
