from rply.errors import ParsingError


class LRParser(object):
    def __init__(self, lr_table, error_handler):
        self.lr_table = lr_table
        self.error_handler = error_handler

    def parse(self, tokenizer):
        from rply.token import Token

        lookahead = None
        lookaheadstack = []
        error_count = 0

        statestack = [0]
        symstack = [Token("$end", None)]

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
                    statestack.append(t)
                    state = t
                    symstack.append(lookahead)
                    lookahead = None
                    if error_count:
                        error_count -= 1
                    continue
                elif t < 0:
                    # reduce a symbol on the stack and emit a production
                    p = self.lr_table.grammar.productions[-t]
                    pname = p.name
                    plen = p.getlength()
                    start = len(symstack) + (-plen - 1)
                    assert start >= 0
                    targ = symstack[start:]
                    del targ[0]
                    start = len(symstack) + (-plen)
                    assert start >= 0
                    del symstack[start:]
                    del statestack[start:]
                    value = p.func(targ)
                    symstack.append(value)
                    state = self.lr_table.lr_goto[statestack[-1]][pname]
                    statestack.append(state)
                    continue
                else:
                    n = symstack[-1]
                    return n
            else:
                # TODO: actual error handling here
                if self.error_handler is not None:
                    self.error_handler(lookahead)
                    raise AssertionError("For now, error_handler must raise.")
                else:
                    raise ParsingError(lookahead.getsourcepos())
