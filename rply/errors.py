class ParserGeneratorError(Exception):
    pass


class ParsingError(Exception):
    def __init__(self, source_pos):
        self.source_pos = source_pos

    def getsourcepos(self):
        return self.source_pos


class ParserGeneratorWarning(Warning):
    pass
