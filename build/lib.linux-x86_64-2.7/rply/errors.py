class ParserGeneratorError(Exception):
    pass


class LexingError(Exception):
    """
    Raised by a Lexer, if no rule matches.
    """
    def __init__(self, message, source_pos):
        self.message = message
        self.source_pos = source_pos

    def getsourcepos(self):
        """
        Returns the position in the source, at which this error occurred.
        """
        return self.source_pos

    def __repr__(self):
        return 'LexingError(%r, %r)' % (self.message, self.source_pos)


class ParsingError(Exception):
    """
    Raised by a Parser, if no production rule can be applied.
    """
    def __init__(self, message, source_pos):
        self.message = message
        self.source_pos = source_pos

    def getsourcepos(self):
        """
        Returns the position in the source, at which this error occurred.
        """
        return self.source_pos

    def __repr__(self):
        return 'ParsingError(%r, %r)' % (self.message, self.source_pos)


class ParserGeneratorWarning(Warning):
    pass
