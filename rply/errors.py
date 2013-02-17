class ParserGeneratorError(Exception):
    pass


class LexingError(Exception):
    def __init__(self, message, source_pos):
        self.message = message
        self.source_pos = source_pos

    def getsourcepos(self):
        return self.source_pos


class ParsingError(Exception):
    def __init__(self, message, source_pos):
        self.message = message
        self.source_pos = source_pos

    def getsourcepos(self):
        return self.source_pos


class ParserGeneratorWarning(Warning):
    pass
