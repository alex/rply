from rply import ParserGenerator
from rply.errors import ParserGeneratorWarning

from .base import BaseTests


class TestWarnings(BaseTests):
    def test_shift_reduce(self):
        pg = ParserGenerator([
            "NAME", "NUMBER", "EQUALS", "PLUS", "MINUS", "TIMES", "DIVIDE",
            "LPAREN", "RPAREN"
        ])

        @pg.production("statement : NAME EQUALS expression")
        def statement_assign(p):
            pass

        @pg.production("statement : expression")
        def statement_expression(p):
            pass

        @pg.production("expression : expression PLUS expression")
        @pg.production("expression : expression MINUS expression")
        @pg.production("expression : expression TIMES expression")
        @pg.production("expression : expression DIVIDE expression")
        def expression_binop(p):
            pass

        @pg.production("expression : MINUS expression")
        def expression_uminus(p):
            pass

        @pg.production("expression : LPAREN expression RPAREN")
        def expression_group(p):
            pass

        @pg.production("expression : NUMBER")
        def expression_number(p):
            pass

        @pg.production("expression : NAME")
        def expression_name(p):
            pass

        with self.assert_warns(
            ParserGeneratorWarning, "20 shift/reduce conflicts"
        ):
            pg.build()

    def test_reduce_reduce(self):
        pg = ParserGenerator(["NAME", "EQUALS", "NUMBER"])

        @pg.production("main : assign")
        def main(p):
            pass

        @pg.production("assign : NAME EQUALS expression")
        @pg.production("assign : NAME EQUALS NUMBER")
        def assign(p):
            pass

        @pg.production("expression : NUMBER")
        def expression(p):
            pass

        with self.assert_warns(
            ParserGeneratorWarning, "1 reduce/reduce conflict"
        ):
            pg.build()

    def test_unused_tokens(self):
        pg = ParserGenerator(["VALUE", "OTHER"])

        @pg.production("main : VALUE")
        def main(p):
            return p[0]

        with self.assert_warns(
            ParserGeneratorWarning, "Token 'OTHER' is unused"
        ):
            pg.build()

    def test_unused_production(self):
        pg = ParserGenerator(["VALUE", "OTHER"])

        @pg.production("main : VALUE")
        def main(p):
            return p[0]

        @pg.production("unused : OTHER")
        def unused(p):
            pass

        with self.assert_warns(
            ParserGeneratorWarning, "Production 'unused' is not reachable"
        ):
            pg.build()
