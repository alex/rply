import os
import tempfile

import py

from rply import DirectoryCache, ParserGenerator, Token
from rply.errors import ParserGeneratorError

from .base import BaseTests


class TestParserGenerator(BaseTests):
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

    def test_nonexistant_precedence(self):
        pg = ParserGenerator(["VALUE"])

        @pg.production("main : VALUE", precedence="abc")
        def main(p):
            pass

        with py.test.raises(ParserGeneratorError):
            pg.build()

    def test_error_symbol(self):
        pg = ParserGenerator(["VALUE"])

        @pg.production("main : VALUE")
        def main(p):
            pass

        @pg.production("main : error")
        def main_error(p):
            pass

        pg.build()


class TestParserCaching(object):
    def test_simple_caching(self):
        pg = ParserGenerator(["VALUE"], cache=DirectoryCache('simple'))

        @pg.production("main : VALUE")
        def main(p):
            return p[0]

        pg.build()
        parser = pg.build()

        assert parser.parse(iter([
            Token("VALUE", "3")
        ])) == Token("VALUE", "3")

    def test_directory(self):
        cache = DirectoryCache(cache_dir=tempfile.gettempdir())
        pg = ParserGenerator(["VALUE"], cache=cache)

        @pg.production("main : VALUE")
        def main(p):
            return p[0]

        pg.build()
        parser = pg.build()

        assert parser.parse(iter([
            Token("VALUE", "3")
        ])) == Token("VALUE", "3")

    def test_full(self):
        cache = DirectoryCache('full', tempfile.gettempdir())
        pg = ParserGenerator(["VALUE"], cache=cache)

        @pg.production("main : VALUE")
        def main(p):
            return p[0]

        pg.build()
        parser = pg.build()

        assert parser.parse(iter([
            Token("VALUE", "3")
        ])) == Token("VALUE", "3")

    def test_directory_nonexist(self):
        cache_dir = os.path.join(tempfile.gettempdir(), "nonexist")
        with py.test.raises(ValueError):
            DirectoryCache('simple', cache_dir)

    def test_invalid_dir(self):
        with py.test.raises(ValueError):
            DirectoryCache(cache_dir=[])

    def test_invalid_id(self):
        with py.test.raises(ValueError):
            DirectoryCache([])
