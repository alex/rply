import re

try:
    import rpython
    from rpython.rtyper.extregistry import ExtRegistryEntry
except ImportError:
    rpython = None

from rply.lexer import Lexer


class Rule(object):
    def __init__(self, name, pattern):
        self.name = name
        self.re = re.compile(pattern)

    def matches(self, s, pos):
        m = self.re.match(s, pos)
        return Match(*m.span(0)) if m is not None else None


class Match(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end


class LexerGenerator(object):
    def __init__(self):
        self.rules = []

    def add(self, name, pattern):
        self.rules.append(Rule(name, pattern))

    def build(self):
        return Lexer(self.rules)

if rpython:
    class RuleEntry(ExtRegistryEntry):
        _type_ = Rule
