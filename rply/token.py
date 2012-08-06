class BaseBox(object):
    def gettokentype(self):
        raise NotImplementedError


class Token(BaseBox):
    def __init__(self, name, value):
        BaseBox.__init__(self)
        self.name = name
        self.value = value

    def gettokentype(self):
        return self.name
