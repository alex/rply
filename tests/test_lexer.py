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

        with raises(StopIteration):
            stream.next()

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

        with raises(StopIteration):
            stream.next()

    def test_position(self):
        lg = LexerGenerator()
        lg.add("NUMBER", r"\d+")
        lg.add("PLUS", r"\+")
        lg.ignore(r"\s+")

        l = lg.build()

        stream = l.lex("2 + 3")
        t = stream.next()
        assert t.source_pos.lineno == 1
        assert t.source_pos.colno == 1
        t = stream.next()
        assert t.source_pos.lineno == 1
        assert t.source_pos.colno == 3
        t = stream.next()
        assert t.source_pos.lineno == 1
        assert t.source_pos.colno == 5
        with raises(StopIteration):
            stream.next()

        stream = l.lex("2 +\n    37")
        t = stream.next()
        assert t.source_pos.lineno == 1
        assert t.source_pos.colno == 1
        t = stream.next()
        assert t.source_pos.lineno == 1
        assert t.source_pos.colno == 3
        t = stream.next()
        assert t.source_pos.lineno == 2
        assert t.source_pos.colno == 5
        with raises(StopIteration):
            stream.next()

    def test_grouping(self):
        lg = LexerGenerator()
        lg.add('TEXT', r"""(?s)(b?r?)(["'])((?:\\.|(?!\2).)*)\2""")

        l = lg.build()

        stream = l.lex('''r"Hello world!"''')
        t = stream.next()

        assert t.name == 'TEXT'
        assert t.groups[0] == 'r'
        assert t.groups[1] == '"'
        assert t.groups[2] == 'Hello world!'

        with raises(StopIteration):
            stream.next()
