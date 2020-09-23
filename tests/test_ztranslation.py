import re

import py

try:
    from rpython.rtyper.test.test_llinterp import interpret
except ImportError:
    pytestmark = py.test.mark.skip("Needs RPython to be on the PYTHONPATH")

from rply import LexerGenerator, ParserGenerator, Token
from rply.errors import ParserGeneratorWarning

from .base import BaseTests
from .utils import BoxInt, ParserState


class BaseTestTranslation(BaseTests):
    def test_basic_lexer(self):
        lg = LexerGenerator()
        lg.add("NUMBER", r"\d+")
        lg.add("PLUS", r"\+")

        l = lg.build()

        def f(n):
            tokens = l.lex("%d+%d+%d" % (n, n, n))
            i = 0
            s = 0
            while i < 5:
                t = tokens.next()
                if i % 2 == 0:
                    if t.name != "NUMBER":
                        return -1
                    s += int(t.value)
                else:
                    if t.name != "PLUS":
                        return -2
                    if t.value != "+":
                        return -3
                i += 1

            ended = False
            try:
                tokens.next()
            except StopIteration:
                ended = True

            if not ended:
                return -4

            return s

        assert self.run(f, [14]) == 42

    def test_regex_flags(self):
        lg = LexerGenerator()
        lg.add("ALL", r".*", re.DOTALL)

        l = lg.build()

        def f(n):
            tokens = l.lex("%d\n%d" % (n, n))

            t = tokens.next()
            if t.name != "ALL":
                return -1

            ended = False
            try:
                tokens.next()
            except StopIteration:
                ended = True

            if not ended:
                return -2

            return 1

        assert self.run(f, [3]) == 1

    def test_basic_parser(self):
        pg = ParserGenerator(["NUMBER", "PLUS"])

        @pg.production("main : expr")
        def main(p):
            return p[0]

        @pg.production("expr : expr PLUS expr")
        def expr_op(p):
            return BoxInt(p[0].getint() + p[2].getint())

        @pg.production("expr : NUMBER")
        def expr_num(p):
            return BoxInt(int(p[0].getstr()))

        with self.assert_warns(
            ParserGeneratorWarning, "1 shift/reduce conflict"
        ):
            parser = pg.build()

        def f(n):
            return parser.parse(iter([
                Token("NUMBER", str(n)),
                Token("PLUS", "+"),
                Token("NUMBER", str(n))
            ])).getint()

        assert self.run(f, [12]) == 24

    def test_parser_state(self):
        pg = ParserGenerator(["NUMBER", "PLUS"], precedence=[
            ("left", ["PLUS"]),
        ])

        @pg.production("main : expression")
        def main(state, p):
            state.count += 1
            return p[0]

        @pg.production("expression : expression PLUS expression")
        def expression_plus(state, p):
            state.count += 1
            return BoxInt(p[0].getint() + p[2].getint())

        @pg.production("expression : NUMBER")
        def expression_number(state, p):
            state.count += 1
            return BoxInt(int(p[0].getstr()))

        parser = pg.build()

        def f():
            state = ParserState()
            return parser.parse(iter([
                Token("NUMBER", "10"),
                Token("PLUS", "+"),
                Token("NUMBER", "12"),
                Token("PLUS", "+"),
                Token("NUMBER", "-2"),
            ]), state=state).getint() + state.count

        assert self.run(f, []) == 26


class TestTranslation(BaseTestTranslation):
    def run(self, func, args):
        return interpret(func, args)


class TestUntranslated(BaseTestTranslation):
    def run(self, func, args):
        return func(*args)
