import py

try:
    from pypy.rpython.test.test_llinterp import interpret
except ImportError:
    py.test.skip('Needs PyPy to be on the PYTHONPATH')

from rply import ParserGenerator, Token
from rply.errors import ParserGeneratorWarning

from .base import BaseTests
from .utils import FakeLexer, BoxInt, ParserState


class TestTranslation(BaseTests):
    def run(self, func, args):
        return interpret(func, args)

    def test_basic(self):
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

        with self.assert_warns(ParserGeneratorWarning, "1 shift/reduce conflict"):
            parser = pg.build()

        def f(n):
            return parser.parse(FakeLexer([
                Token("NUMBER", str(n)),
                Token("PLUS", "+"),
                Token("NUMBER", str(n))
            ])).getint()

        assert self.run(f, [12]) == 24

    def test_state(self):
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
            return parser.parse(FakeLexer([
                Token("NUMBER", "10"),
                Token("PLUS", "+"),
                Token("NUMBER", "12"),
                Token("PLUS", "+"),
                Token("NUMBER", "-2"),
            ]), state=state).getint() + state.count

        assert self.run(f, []) == 26
