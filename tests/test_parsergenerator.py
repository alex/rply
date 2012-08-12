import py

from rply import ParserGenerator
from rply.errors import ParserGeneratorError, ParserGeneratorWarning

from .base import BaseTests


class TestParserGenerator(BaseTests):
    def test_simple(self):
        pg = ParserGenerator(["VALUE"])

        @pg.production("main : VALUE")
        def main(p):
            return p[0]

        parser = pg.build()

        assert parser.lr_table.lr_action == {
            0: {"VALUE": 2},
            1: {"$end": 0},
            2: {"$end": -1},
        }

    def test_empty_production(self):
        pg = ParserGenerator(["VALUE"])

        @pg.production("main : values")
        def main(p):
            return p[0]

        @pg.production("values : VALUE values")
        def values_value(p):
            return [p[0]] + p[1]

        @pg.production("values :")
        def values_empty(p):
            return []

        parser = pg.build()
        assert parser.lr_table.lr_action == {
            0: {"$end": -3, "VALUE": 3},
            1: {"$end": 0},
            2: {"$end": -1},
            3: {"$end": -3, "VALUE": 3},
            4: {"$end": -2},
        }

    def test_production_syntax_error(self):
        pg = ParserGenerator([])
        with py.test.raises(ParserGeneratorError):
            pg.production("main VALUE")

    def test_production_terminal_overlap(self):
        pg = ParserGenerator(["VALUE"])

        @pg.production("VALUE :")
        def x(p):
            pass

        with py.test.raises(ParserGeneratorError):
            pg.build()

    def test_duplicate_precedence(self):
        pg = ParserGenerator([], precedence=[
            ("left", ["term", "term"])
        ])

        with py.test.raises(ParserGeneratorError):
            pg.build()

    def test_invalid_associativity(self):
        pg = ParserGenerator([], precedence=[
            ("to-the-left", ["term"]),
        ])

        with py.test.raises(ParserGeneratorError):
            pg.build()
