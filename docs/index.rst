RPLY
====

Welcome to RPLY! A pure python parser generator, that also works with RPython.
It is a more-or-less direct port of David Beazley's awesome PLY, with a new
public API, and RPython support.

Basic API:

.. code:: python

    from rply import ParserGenerator, LexerGenerator
    from rply.token import BaseBox

    lg = LexerGenerator()
    # Add takes a rule name, and a regular expression that defines the rule.
    lg.add("PLUS", r"\+")
    lg.add("MINUS", r"-")
    lg.add("NUMBER", r"\d+")

    lg.ignore(r"\s+")

    # This is a list of the token names. precedence is an optional list of
    # tuples which specifies order of operation for avoiding ambiguity.
    # precedence must be one of "left", "right", "nonassoc".
    # cache_id is an optional string which specifies an ID to use for
    # caching. It should *always* be safe to use caching,
    # RPly will automatically detect when your grammar is
    # changed and refresh the cache for you.
    pg = ParserGenerator(["NUMBER", "PLUS", "MINUS"],
            precedence=[("left", ['PLUS', 'MINUS'])], cache_id="myparser")

    @pg.production("main : expr")
    def main(p):
        # p is a list, of each of the pieces on the right hand side of the
        # grammar rule
        return p[0]

    @pg.production("expr : expr PLUS expr")
    @pg.production("expr : expr MINUS expr")
    def expr_op(p):
        lhs = p[0].getint()
        rhs = p[2].getint()
        if p[1].gettokentype() == "PLUS":
            return BoxInt(lhs + rhs)
        elif p[1].gettokentype() == "MINUS":
            return BoxInt(lhs - rhs)
        else:
            raise AssertionError("This is impossible, abort the time machine!")

    @pg.production("expr : NUMBER")
    def expr_num(p):
        return BoxInt(int(p[0].getstr()))

    lexer = lg.build()
    parser = pg.build()

    class BoxInt(BaseBox):
        def __init__(self, value):
            self.value = value

        def getint(self):
            return self.value

Then you can do:

.. code:: python

    parser.parse(lexer.lex("1 + 3 - 2+12-32"))

You can also substitute your own lexer. A lexer is an object with a ``next()``
method that returns either the next token in sequence, or ``None`` if the token
stream has been exhausted.

Why do we have the boxes?
-------------------------

In RPython, like other statically typed languages, a variable must have a
specific type, we take advantage of polymorphism to keep values in a box so
that everything is statically typed. You can write whatever boxes you need for
your project.

If you don't intend to use your parser from RPython, and just want a cool pure
Python parser you can ignore all the box stuff and just return whatever you
like from each production method.

Error handling
--------------

By default, when a parsing error is encountered, an :exc:`rply.ParsingError` is
raised, it has a method :meth:`~rply.ParsingError.getsourcepos()`, which
returns an :class:`rply.token.SourcePosition` object.

You may also provide an error handler, which, at the moment, must raise an
exception. It receives the :class:`~rply.Token` object that the parser errored
on.

.. code:: python

    pg = ParserGenerator(...)

    @pg.error
    def error_handler(token):
        raise ValueError("Ran into a %s where it wasn't expected" % token.gettokentype())


User's Guide
------------

.. toctree::

   users-guide/lexers.rst
   users-guide/parsers.rst


API Documentation
-----------------

The API documentation provides detailed information on the functions, classes
and methods, provided by RPly. If you are looking for something specific,
take a look at one of these documents:

.. toctree::

   api/rply.rst
   api/token.rst


Additional Information
----------------------

Everything not directly related to the usage of RPly.

.. toctree::

   additional/license.rst
