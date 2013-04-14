from rply.token import BaseBox


class RecordingLexer(object):
    def __init__(self, record, tokens):
        self.tokens = iter(tokens)
        self.record = record

    def next(self):
        s = "None"
        try:
            token = next(self.tokens)
            s = token.gettokentype()
        finally:
            self.record.append("token:%s" % s)

        return token

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()


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
