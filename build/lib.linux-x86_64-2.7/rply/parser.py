from rply.errors import ParsingError


class LRParser(object):
    def __init__(self, lr_table, error_handler):
        self.lr_table = lr_table
        self.error_handler = error_handler

    def parse(self, tokenizer, state=None):
        from rply.token import Token

        lookahead = None
        lookaheadstack = []

        statestack = [0]
        symstack = [Token("$end", "$end")]

        current_state = 0
        while True:
            if self.lr_table.default_reductions[current_state]:
                t = self.lr_table.default_reductions[current_state]
                current_state = self._reduce_production(
                    t, symstack, statestack, state
                )
                continue

            if lookahead is None:
                if lookaheadstack:
                    lookahead = lookaheadstack.pop()
                else:
                    try:
                        lookahead = next(tokenizer)
                    except StopIteration:
                        lookahead = None

                if lookahead is None:
                    lookahead = Token("$end", "$end")

            ltype = lookahead.gettokentype()
            if ltype in self.lr_table.lr_action[current_state]:
                t = self.lr_table.lr_action[current_state][ltype]
                if t > 0:
                    statestack.append(t)
                    current_state = t
                    symstack.append(lookahead)
                    lookahead = None
                    continue
                elif t < 0:
                    current_state = self._reduce_production(
                        t, symstack, statestack, state
                    )
                    continue
                else:
                    n = symstack[-1]
                    return n
            else:
                # TODO: actual error handling here
                if self.error_handler is not None:
                    if state is None:
                        self.error_handler(lookahead)
                    else:
                        self.error_handler(state, lookahead)
                    raise AssertionError("For now, error_handler must raise.")
                else:
                    raise ParsingError(None, lookahead.getsourcepos())

    def _reduce_production(self, t, symstack, statestack, state):
        # reduce a symbol on the stack and emit a production
        p = self.lr_table.grammar.productions[-t]
        pname = p.name
        plen = p.getlength()
        start = len(symstack) + (-plen - 1)
        assert start >= 0
        targ = symstack[start + 1:]
        start = len(symstack) + (-plen)
        assert start >= 0
        del symstack[start:]
        del statestack[start:]
        if state is None:
            value = p.func(targ)
        else:
            value = p.func(state, targ)
        symstack.append(value)
        current_state = self.lr_table.lr_goto[statestack[-1]][pname]
        statestack.append(current_state)
        return current_state
