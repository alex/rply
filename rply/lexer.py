from rply.errors import LexingError
from rply.token import SourcePosition, Token


class Lexer(object):
    def __init__(self, rules, ignore_rules):
        self.rules = rules
        self.ignore_rules = ignore_rules

    def lex(self, s):
        return LexerStream(self, s)


class LexerStream(object):
    def __init__(self, lexer, s):
        self.lexer = lexer
        self.s = s
        self.idx = 0
        self.lineno = 1
        self.last_pos = 0

    def __iter__(self):
        return self

    def next(self):
        if self.idx >= len(self.s):
            raise StopIteration
        for rule in self.lexer.ignore_rules:
            match = rule.matches(self.s, self.idx)
            if match:
                self.idx = match.end
                return self.next()
        for rule in self.lexer.rules:
            match = rule.matches(self.s, self.idx)
            if match:
                source_pos = self.get_position(match.start)
                token = Token(rule.name, self.s[match.start:match.end], source_pos)
                self.idx = match.end
                return token
        else:
            raise LexingError(None, SourcePosition(self.idx, -1, -1))

    def __next__(self):
        return self.next()

    def get_position(self, cursor):
        """ Returns a SourcePosition object containing the current cursor position
        and the associated line and column number

        """

        self.lineno += self.s.count("\n", self.last_pos, cursor)

        if self.lineno > 1:
            colno = cursor - self.s.rfind("\n", 0, cursor)
        else:
            colno = cursor + 1

        sp = SourcePosition(cursor, self.lineno, colno)
        self.last_pos = cursor

        return sp

    def __str__(self):
        """ Returns a string representation of the LexerStream as a list.

        As a side-effect the LexerStream needs to process the whole stream,
        thus we need to restore the positioning information after generating
        the representation.
        """

        old_idx, old_last_pos, old_lineno = self.idx, self.last_pos, self.lineno
        out = str(list(self))
        self.idx, self.last_pos, self.lineno =old_idx, old_last_pos, old_lineno

        return out
