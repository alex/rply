from rply import ParserGenerator


class TestParserBuilder(object):
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
