from rply import ParserGenerator, Token

from .utils import FakeLexer


class TestBasic(object):
    def test_simplest(self):
        pg = ParserGenerator(["VALUE"])

        @pg.production("main : VALUE")
        def main(p):
            return p[0]

        parser = pg.build()

        assert parser.parse(FakeLexer([Token("VALUE", "abc")])) == "abc"
