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
        self.linebreaks = [-1] + [i for i, letter in enumerate(s) if letter == '\n']

    def source_position(self, position):
        lineno = 0
        broken = False
        for lineno, linebreak in enumerate(self.linebreaks):
            if position < linebreak:
                broken = True
                break

        if not broken:
            lineno += 1

        return SourcePosition(position, lineno, (position - self.linebreaks[lineno-1]))

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
                source_pos = self.source_position(match.start)
                token = Token(rule.name, self.s[match.start:match.end], source_pos)
                self.idx = match.end
                return token
        else:
            raise LexingError(None, SourcePosition(self.idx, -1, -1))
