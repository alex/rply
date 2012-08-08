from rply.token import BaseBox


class FakeLexer(object):
    def __init__(self, tokens):
        self.tokens = iter(tokens)

    def next(self):
        try:
            return self.tokens.next()
        except StopIteration:
            return None


class BoxInt(BaseBox):
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other.value

    def getint(self):
        return self.value
