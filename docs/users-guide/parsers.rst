Generating Parsers
==================

In this part of the tutorial we will generate a parser for simple mathematical
expressions as defined by the following BNF_ grammar::

    <expression> ::= "\d+"
                   | <expression> "+" <expression>
                   | <expression> "-" <expression>
                   | <expression> "*" <expression>
                   | <expression> "/" <expression>
                   | "(" <expression> ")"


.. _BNF: https://en.wikipedia.org/wiki/Backus-Naur_Form


Furthermore we use the following lexer:

.. code:: python

    from rply import LexerGenerator

    lg = LexerGenerator()

    lg.add('NUMBER', r'\d+')
    lg.add('PLUS', r'\+')
    lg.add('MINUS', r'-')
    lg.add('MUL', r'\*')
    lg.add('DIV', r'/')
    lg.add('OPEN_PARENS', r'\(')
    lg.add('CLOSE_PARENS', r'\)')

    lg.ignore('\s+')

    lexer = lg.build()


Before we begin working on the parser, we define ourselves an abstract syntax
tree:

.. code:: python

    from rply.token import BaseBox

    class Number(BaseBox):
        def __init__(self, value):
            self.value = value

        def eval(self):
            return self.value

    class BinaryOp(BaseBox):
        def __init__(self, left, right):
            self.left = left
            self.right = right

    class Add(BinaryOp):
        def eval(self):
            return self.left.eval() + self.right.eval()

    class Sub(BinaryOp):
        def eval(self):
            return self.left.eval() - self.right.eval()

    class Mul(BinaryOp):
        def eval(self):
            return self.left.eval() * self.right.eval()

    class Div(BinaryOp):
        def eval(self):
            return self.left.eval() / self.right.eval()


In RPython variables must have a specific type, so we use polymorphism with
:class:`~rply.token.BaseBox` to ensure that. In your own code you can achieve
the same by inheriting from :class:`~rply.token.BaseBox` as we did here. If
you are not writing RPython code, you can ignore this completely.

Having covered all that we actually start working on the parser itself:


.. code:: python

    from rply import ParserGenerator

    pg = ParserGenerator(
        # A list of all token names, accepted by the parser.
        ['NUMBER', 'OPEN_PARENS', 'CLOSE_PARENS',
         'PLUS', 'MINUS', 'MUL', 'DIV'
        ],
        # A list of precedence rules with ascending precedence, to
        # disambiguate ambiguous production rules.
        precedence=[
            ('left', ['PLUS', 'MINUS']),
            ('left', ['MUL', 'DIV'])
        ]
    )

    @pg.production('expression : NUMBER')
    def expression_number(p):
        # p is a list of the pieces matched by the right hand side of the
        # rule
        return Number(int(p[0].getstr()))

    @pg.production('expression : OPEN_PARENS expression CLOSE_PARENS')
    def expression_parens(p):
        return p[1]

    @pg.production('expression : expression PLUS expression')
    @pg.production('expression : expression MINUS expression')
    @pg.production('expression : expression MUL expression')
    @pg.production('expression : expression DIV expression')
    def expression_binop(p):
        left = p[0]
        right = p[2]
        if p[1].gettokentype() == 'PLUS':
            return Add(left, right)
        elif p[1].gettokentype() == 'MINUS':
            return Sub(left, right)
        elif p[1].gettokentype() == 'MUL':
            return Mul(left, right)
        elif p[1].gettokentype() == 'DIV':
            return Div(left, right)
        else:
            raise AssertionError('Oops, this should not be possible!')

    parser = pg.build()

As you can see production rules define a sequence of terminals (tokens) and
non-terminals (intermediate values, in this case only `expression`) using
the :meth:`~rply.ParserGenerator.production` decorator. The function
receives a list of the tokens and non-terminals and returns a non-terminal.

It is possible to chain multiple production rule right-hand sides with "|".
Thus, the following are equivalent:

.. code:: python

    from rply import ParserGenerator

    pg = ParserGenerator(["TOK1", "TOK2"])

    @pg.production("rule: TOK1")
    @pg.production("rule: TOK2")
    def prod(p):
        pass

    @pg.production("rule: TOK1 | TOK2")
    def prod_shorthand(p):
        pass


In this case we create an abstract syntax tree. We can now use this parser in
combination with the lexer given to parse and evaluate mathematical expressions
as defined by our grammar::

    >>> parser.parse(lexer.lex('1 + 1')).eval()
    2
    >>> parser.parse(lexer.lex('1 + 2 * 3')).eval()
    7


Error Handling
--------------

As long as we parse code that is well formed according to our grammar, all is
fine but one of the more difficult problems in writing a parser is handling
errors.

Per default in case of an error you get a :exc:`rply.ParsingError`::

    >>> parser.parse(lexer.lex('1 1'))

This error will not provide any information apart from the position at which
it occurred accessible through :meth:`~rply.ParsingError.getsourcepos`.

While it is not possible to recover from an error, you can define your own
error handler:

.. code:: python

    @pg.error
    def error_handler(token):
        raise ValueError("Ran into a %s where it wasn't expected" % token.gettokentype())

The `token` passed to the error handler will be the token the parser errored
on.


Maintaining State
-----------------

Sometimes it can be useful to have additional state within the parser, for
example as a way to pass information to the parser about the name of the file
currently being parsed.

In order to do this we simply define a state object to pass around:

.. code:: python

    class ParserState(object):
        def __init__(self, filename):
            self.filename = filename

We can pass `ParserState` objects to the parser simply like this:

.. code:: python

    parser.parse(lexer.lex(source), state=ParserState('foo.py'))

This will call every production rule and the error handler with the
`ParserState` instance as first argument.


Precedence on rules
-------------------

Sometimes it is useful to give a rule a manual precedence. For this pass the
`precedence` argument to `production`. For example, if we  wanted to add an
implicit multiplication rule to the above language (so that e.g. `16 32` is
parsed the same as `16 * 32`) we use the following:

.. code:: python

    @pg.production('expression : expression expression', precedence='MUL')
    def implicit_multiplication(p):
        return Mul(p[0], p[1])
