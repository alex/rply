from rply import ParserGenerator, Token


class TestBasic(object):
    def test_simplest(self):
        pg = ParserGenerator(["VALUE"])

        @pg.production("main : VALUE")
        def main(p):
            return p[0]

        parser = pg.build()

        assert parser.parse(iter([Token("VALUE", "abc")])) == "abc"
