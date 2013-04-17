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
        self.last_break = 0
        self.lineno = 1

    def __iter__(self):
        return self

    def next(self):
        if self.idx >= len(self.s):
            raise StopIteration
        for rule in self.lexer.ignore_rules:
            match = rule.matches(self.s, self.idx)
            if match:
                self.__update_lineno__(match.end)                
                self.idx = match.end
                return self.next()
        for rule in self.lexer.rules:
            match = rule.matches(self.s, self.idx)
            if match:
                self.__update_lineno__(match.end)
                source_pos = SourcePosition(match.start, 
                                            self.lineno, 
                                            match.start - self.last_break + 1)
                token = Token(rule.name, self.s[match.start:match.end], source_pos)
                self.idx = match.end
                return token
        else:
            raise LexingError(None, SourcePosition(self.idx, -1, -1))

    def __next__(self):
        return self.next()

    def __repr__(self):
        """ Returns a string representation of the LexerStream as a list.
        
        As a side-effect the LexerStream needs to process the whole stream, 
        thus we need to restore the positioning information after generating
        the representation.
        """

        old_idx = self.idx
        old_lineno = self.lineno
        old_last_break = self.last_break

        out = str(list(self))

        self.idx = old_idx
        self.lineno = old_lineno
        self.last_break = old_last_break
        return out

    def __update_lineno__(self, cursor):
        """ Updates the lineno by counting how many line breaks ('\n') there are 
        between the current cursor position and the last break. 
        """
        assert self.last_break >= 0
        if self.s.rfind("\n", 0, cursor) >= self.last_break:
            self.lineno += self.s.count("\n", self.last_break, cursor)
            self.last_break = self.s.rfind("\n", 0, cursor) + 1
