from rply.token import BaseBox


class FakeLexer(object):
    def __init__(self, tokens):
        self.tokens = iter(tokens)

    def next(self):
        try:
            return next(self.tokens)
        except StopIteration:
            return None


class BoxInt(BaseBox):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "%s(%d)" % (self.__class__.__name__, self.value)

    def __eq__(self, other):
        return self.value == other.value

    def getint(self):
        return self.value


class ParserState(object):
    def __init__(self):
        self.count = 0
