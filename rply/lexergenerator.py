import re


class LexerGenerator(object):
    def __init__(self):
        self.rules = []

    def add(self, name, pattern):
        self.rules.append((name, re.compile(pattern)))

    def build(self):
        pass
