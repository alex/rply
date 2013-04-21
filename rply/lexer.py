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
                source_pos = self.__get_position__(match.start)
                token = Token(rule.name, self.s[match.start:match.end], source_pos)
                self.idx = match.end
                return token
        else:
            raise LexingError(None, SourcePosition(self.idx, -1, -1))

    def __next__(self):
        return self.next()


    def __get_position__(self, cursor):
        """ Returns a SourcePosition object containing the current cursor position
        and the associated line and column number

        This implementation scans the whole string every time it is called.
        """

        lineno = self.s.count("\n", 0, cursor) + 1

        colno = cursor + 1
        if lineno > 1:
            colno = colno - (self.s.rfind("\n", 0, cursor)+1)

        sp = SourcePosition(cursor, lineno, colno)

        return sp
