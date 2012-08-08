class BaseBox(object):
    def gettokentype(self):
        raise NotImplementedError


class Token(BaseBox):
    def __init__(self, name, value):
        BaseBox.__init__(self)
        self.name = name
        self.value = value

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value

    def gettokentype(self):
        return self.name


class ProductionSymbol(BaseBox):
    def __init__(self, name, value):
        BaseBox.__init__(self)
        self.name = name
        self.value = value

    def gettokentype(self):
        return self.name
