class FakeLexer(object):
    def __init__(self, tokens):
        self.tokens = iter(tokens)

    def next(self):
        try:
            return self.tokens.next()
        except StopIteration:
            return None
