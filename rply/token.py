class BaseBox(object):
    _attrs_ = []


class Token(BaseBox):
    def __init__(self, name, value, source_pos=None):
        self.name = name
        self.value = value
        self.source_pos = source_pos

    def __repr__(self):
        return "Token(%r, %r)" % (self.name, self.value)

    def __eq__(self, other):
        if not isinstance(other, Token):
            return NotImplemented
        return self.name == other.name and self.value == other.value

    def gettokentype(self):
        return self.name

    def getsourcepos(self):
        return self.source_pos

    def getstr(self):
        return self.value


class SourcePosition(object):
    def __init__(self, idx, lineno, colno):
        self.idx = idx
        self.lineno = lineno
        self.colno = colno
