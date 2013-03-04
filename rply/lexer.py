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

    def next(self):
        if self.idx >= len(self.s):
            return None
        for rule in self.lexer.ignore_rules:
            match = rule.matches(self.s, self.idx)
            if match:
                self.idx = match.end
                return self.next()
        for rule in self.lexer.rules:
            match = rule.matches(self.s, self.idx)
            if match:
                # TODO: lineno and colno
                source_pos = SourcePosition(match.start, -1, -1)
                token = Token(rule.name, self.s[match.start:match.end], source_pos)
                self.idx = match.end
                return token
        else:
            raise LexingError(None, SourcePosition(self.idx, -1, -1))
