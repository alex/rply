RPLY
====

.. image:: https://secure.travis-ci.org/alex/rply.png?branch=master

Welcome to RPLY! A pure python parser generator, that also works with RPython.
It is a more-or-less direct port of David Beazley's awesome PLY, with a new
public API, and RPython support. Note that this currently only contains the
``yacc`` half of PLY, ``lex`` is not supported.

Basic API:

.. code:: python

    from rply import ParserGenerator
    from rply.token import BaseBox

    # This is a list of the token names
    pg = ParserGenerator(["NUMBER", "PLUS", "MINUS"])

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
        if p[1].gettokenname() == "PLUS":
            return BoxInt(lhs + rhs)
        elif p[1].gettokenname() = "MINUS":
            return BoxInt(lhs - rhs)
        else:
            raise AssertionError("This is impossible, abort the time machine!")

    @pg.production("expr : NUMBER")
    def expr_num(p):
        return BoxInt(int(p[0].getstr()))

    parser = pg.build()

    class BoxInt(BaseBox):
        def __init__(self, value):
            self.value = value

        def getint(self):
            return self.value

Then you can do:

.. code:: python

    parser.parse(lexer)

Where lexer is an object that defines a ``next()`` method that returns either
the next token in sequence, or ``None``.

Why do we have the boxes?
-------------------------

In RPython, like other statically typed languages, a variable must have a
specific type, we take advantage of polymorphism to keep values in a box so
that everything is statically typed. You can write whatever boxes you need for
your project.

If you don't intend to use your parser from RPython, and just want a cool pure
Python parser you can ignore all the box stuff and just return whatever you like
from each production method.