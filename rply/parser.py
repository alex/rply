class LRParser(object):
    def __init__(self, lr_table):
        self.lr_table = lr_table

    def parse(self, tokenizer):
        from rply import Token

        lookahead = None
        lookaheadstack = []
        error_count = 0

        statestack = []
        symstack = []

        statestack.append(0)
        symstack.append(Token("$end", None))
        state = 0
        while True:
            if lookahead is None:
                if lookaheadstack:
                    lookahead = lookaheadstack.pop()
                else:
                    lookahead = tokenizer.next()

                if lookahead is None:
                    lookahead = Token("$end", None)

            ltype = lookahead.gettokentype()
            if ltype in self.lr_table.lr_action[state]:
                t = self.lr_table.lr_action[state][ltype]
                if t > 0:
                    raise NotImplementedError
                elif t < 0:
                    raise NotImplementedError
                else:
                    raise NotImplementedError
            else:
                raise NotImplementedError
