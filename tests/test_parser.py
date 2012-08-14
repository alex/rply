import operator

import py

from rply import ParserGenerator, Token, ParsingError
from rply.errors import ParserGeneratorWarning

from .base import BaseTests
from .utils import FakeLexer, BoxInt


class TestBasic(BaseTests):
    def test_simple(self):
        pg = ParserGenerator(["VALUE"])

        @pg.production("main : VALUE")
        def main(p):
            return p[0]

        parser = pg.build()

        assert parser.parse(FakeLexer([Token("VALUE", "abc")])) == Token("VALUE", "abc")

    def test_arithmetic(self):
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
        assert parser.parse(FakeLexer([
            Token("NUMBER", "1"),
            Token("PLUS", "+"),
            Token("NUMBER", "4")
        ])) == BoxInt(5)

    def test_null_production(self):
        pg = ParserGenerator(["VALUE", "SPACE"])

        @pg.production("main : values")
        def main(p):
            return p[0]

        @pg.production("values : none")
        def values_empty(p):
            return []

        @pg.production("values : VALUE")
        def values_value(p):
            return [p[0].getstr()]

        @pg.production("values : values SPACE VALUE")
        def values_values(p):
            return p[0] + [p[2].getstr()]

        @pg.production("none :")
        def none(p):
            return None

        parser = pg.build()
        assert parser.parse(FakeLexer([
            Token("VALUE", "abc"),
            Token("SPACE", " "),
            Token("VALUE", "def"),
            Token("SPACE", " "),
            Token("VALUE", "ghi"),
        ])) == ["abc", "def", "ghi"]

        assert parser.parse(FakeLexer([])) == []

    def test_precedence(self):
        pg = ParserGenerator(["NUMBER", "PLUS", "TIMES"], precedence=[
            ("left", ["PLUS"]),
            ("left", ["TIMES"]),
        ])

        @pg.production("main : expr")
        def main(p):
            return p[0]

        @pg.production("expr : expr PLUS expr")
        @pg.production("expr : expr TIMES expr")
        def expr_binop(p):
            return BoxInt({
                "+": operator.add,
                "*": operator.mul
            }[p[1].getstr()](p[0].getint(), p[2].getint()))

        @pg.production("expr : NUMBER")
        def expr_num(p):
            return BoxInt(int(p[0].getstr()))

        parser = pg.build()

        assert parser.parse(FakeLexer([
            Token("NUMBER", "3"),
            Token("TIMES", "*"),
            Token("NUMBER", "4"),
            Token("PLUS",  "+"),
            Token("NUMBER", "5")
        ])) == BoxInt(17)

    def test_per_rule_precedence(self):
        pg = ParserGenerator(["NUMBER", "MINUS"], precedence=[
            ("right", ["UMINUS"]),
        ])

        @pg.production("main : expr")
        def main_expr(p):
            return p[0]

        @pg.production("expr : expr MINUS expr")
        def expr_minus(p):
            return BoxInt(p[0].getint() - p[2].getint())

        @pg.production("expr : MINUS expr", precedence="UMINUS")
        def expr_uminus(p):
            return BoxInt(-p[1].getint())

        @pg.production("expr : NUMBER")
        def expr_number(p):
            return BoxInt(int(p[0].getstr()))

        parser = pg.build()

        assert parser.parse(FakeLexer([
            Token("MINUS", "-"),
            Token("NUMBER", "4"),
            Token("MINUS", "-"),
            Token("NUMBER", "5"),
        ])) == BoxInt(-9)

    def test_parse_error(self):
        pg = ParserGenerator(["VALUE"])

        @pg.production("main : VALUE")
        def main(p):
            return p[0]

        parser = pg.build()

        with py.test.raises(ParsingError):
            parser.parse(FakeLexer([
                Token("VALUE", "hello"),
                Token("VALUE", "world"),
            ]))
