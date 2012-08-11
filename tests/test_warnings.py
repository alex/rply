from rply import ParserGenerator
from rply.errors import ParserGeneratorWarning

from .base import BaseTests


class TestWarnings(BaseTests):
    def test_shift_reduce_warning(self):
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

        with self.assert_warns(ParserGeneratorWarning, "20 shift/reduce conflicts"):
            pg.build()
