from pytest import raises

from rply import LexerGenerator, StackedLexerGenerator


class TestLexer(object):
    lexer_class = LexerGenerator

    def test_simple(self):
        lg = self.lexer_class()
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
        lg = self.lexer_class()
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
        lg = self.lexer_class()
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


class TestStackedLexer(TestLexer):
    lexer_class = StackedLexerGenerator

    def test_transitions(self):
        lg = self.lexer_class()
        lg.add('NUMBER', r'\d+')
        lg.add('ADD', r'\+')
        lg.add('COMMENT_START', r'\(#', transition='push', target='comment')
        lg.ignore(r'\s+')

        comment = lg.add_state('comment')
        comment.add('COMMENT_START', r'\(#', transition='push', target='comment')
        comment.add('COMMENT_END', r'#\)', transition='pop')
        comment.add('COMMENT', r'([^(#]|#(?!\))|\)(?!#))+')

        l = lg.build()

        stream = l.lex('(# this is (# a nested comment #)#) 1 + 1 (# 1 # 1 #)')
        t = stream.next()
        assert t.name == 'COMMENT_START'
        assert t.value == '(#'
        t = stream.next()
        assert t.name == 'COMMENT'
        assert t.value == ' this is '
        t = stream.next()
        assert t.name == 'COMMENT_START'
        assert t.value == '(#'
        t = stream.next()
        assert t.name == 'COMMENT'
        assert t.value == ' a nested comment '
        t = stream.next()
        assert t.name == 'COMMENT_END'
        assert t.value == '#)'
        t = stream.next()
        assert t.name == 'COMMENT_END'
        assert t.value == '#)'
        t = stream.next()
        assert t.name == 'NUMBER'
        assert t.value == '1'
        t = stream.next()
        assert t.name == 'ADD'
        assert t.value == '+'
        t = stream.next()
        assert t.name == 'NUMBER'
        assert t.value == '1'
        t = stream.next()
        assert t.name == 'COMMENT_START'
        assert t.value == '(#'
        t = stream.next()
        assert t.name == 'COMMENT'
        assert t.value == ' 1 # 1 '
        t = stream.next()
        assert t.name == 'COMMENT_END'
        assert t.value == '#)'
