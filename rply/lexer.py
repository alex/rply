from rply.errors import LexingError
from rply.token import SourcePosition, Token


class Lexer(object):
    def __init__(self, start, states):
        self.start = start
        self.states = states

    def lex(self, s):
        return LexerStream(self, s)


class LexerStream(object):
    def __init__(self, lexer, s):
        self.lexer = lexer
        self.s = s
        self.idx = 0

        self._lineno = 1

        self.states = [lexer.start]

    def __iter__(self):
        return self

    def _get_current_state(self):
        return self.states[-1]

    def _make_transition(self, rule):
        if rule.transition is None:
            return
        elif rule.transition == 'push':
            self.states.append(self.lexer.states[rule.target])
        elif rule.transition == 'pop':
            self.states.pop()

    def _update_pos(self, match):
        self.idx = match.end
        self._lineno += self.s.count("\n", match.start, match.end)
        last_nl = self.s.rfind("\n", 0, match.start)
        if last_nl < 0:
            return match.start + 1
        else:
            return match.start - last_nl

    def next(self):
        while True:
            if self.idx >= len(self.s):
                raise StopIteration
            for rule in self._get_current_state().ignore_rules:
                match = rule.matches(self.s, self.idx)
                if match:
                    self._update_pos(match)
                    self._make_transition(rule)
                    break
            else:
                break

        for rule in self._get_current_state().rules:
            match = rule.matches(self.s, self.idx)
            if match:
                lineno = self._lineno
                colno = self._update_pos(match)
                source_pos = SourcePosition(match.start, lineno, colno)
                token = Token(
                    rule.name, self.s[match.start:match.end], source_pos
                )
                self._make_transition(rule)
                return token
        else:
            raise LexingError(None, SourcePosition(self.idx, -1, -1))

    def __next__(self):
        return self.next()
