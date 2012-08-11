import sys
import warnings

from rply.errors import ParserGeneratorError, ParserGeneratorWarning
from rply.grammar import Grammar
from rply.parser import LRParser
from rply.utils import IdentityDict


class ParserGenerator(object):
    def __init__(self, tokens, precedence=[]):
        self.tokens = tokens
        self.productions = []
        self.precedence = precedence

    def production(self, rule):
        parts = rule.split()
        production_name = parts[0]
        if parts[1] != ":":
            raise ParserGeneratorError("Expecting :")
        syms = parts[2:]

        def inner(func):
            self.productions.append((production_name, syms, func))
            return func
        return inner

    def build(self):
        g = Grammar(self.tokens)

        for level, (assoc, terms) in enumerate(self.precedence, 1):
            for term in terms:
                g.set_precedence(term, assoc, level)

        for prod_name, syms, func in self.productions:
            g.add_production(prod_name, syms, func)

        g.set_start()
        g.build_lritems()
        g.compute_first()
        g.compute_follow()

        table = LRTable(g)
        if table.sr_conflicts:
            warnings.warn(
                "%d shift/reduce conflict%s" % (len(table.sr_conflicts), "s" if len(table.sr_conflicts) > 1 else ""),
                ParserGeneratorWarning,
                stacklevel=2,
            )
        if table.rr_conflicts:
            warnings.warn(
                "%d reduce/reduce conflict%s" % (len(table.rr_conflicts), "s" if len(table.rr_conflicts) > 1 else ""),
                ParserGeneratorWarning,
                stacklevel=2,
            )
        return LRParser(table)


def digraph(X, R, FP):
    N = dict.fromkeys(X, 0)
    stack = []
    F = {}
    for x in X:
        if N[x] == 0:
            traverse(x, N, stack, F, X, R, FP)
    return F


def traverse(x, N, stack, F, X, R, FP):
    stack.append(x)
    d = len(stack)
    N[x] = d
    F[x] = FP(x)

    rel = R(x)
    for y in rel:
        if N[y] == 0:
            traverse(y, N, stack, F, X, R, FP)
        N[x] = min(N[x], N[y])
        for a in F.get(y, []):
            if a not in F[x]:
                F[x].append(a)
    if N[x] == d:
        N[stack[-1]] = sys.maxint
        F[stack[-1]] = F[x]
        element = stack.pop()
        while element != x:
            N[stack[-1]] = sys.maxint
            F[stack[-1]] = F[x]
            element = stack.pop()


class LRTable(object):
    def __init__(self, grammar):
        self.grammar = grammar

        self.lr_action = {}
        self.lr_goto = {}
        self._lr_goto_cache = IdentityDict()
        self._lr_other_goto_cache = {}
        self.lr0_cidhash = IdentityDict()

        self._add_count = 0

        self.sr_conflicts = []
        self.rr_conflicts = []

        self.build_table()

    def lr0_items(self):
        C = [self.lr0_closure([self.grammar.productions[0].lr_next])]
        for i, I in enumerate(C):
            self.lr0_cidhash[I] = i

        i = 0
        while i < len(C):
            I = C[i]
            i += 1

            asyms = set()
            for ii in I:
                for s in ii.unique_syms:
                    asyms.add(s)
            for x in asyms:
                g = self.lr0_goto(I, x)
                if not g:
                    continue
                if g in self.lr0_cidhash:
                    continue
                self.lr0_cidhash[g] = len(C)
                C.append(g)
        return C

    def lr0_closure(self, I):
        self._add_count += 1

        J = I[:]
        added = True
        while added:
            added = False
            for j in J:
                for x in j.lr_after:
                    if x.lr0_added == self._add_count:
                        continue
                    J.append(x.lr_next)
                    x.lr0_added = self._add_count
                    added = True
        return J

    def lr0_goto(self, I, x):
        if I in self._lr_goto_cache and x in self._lr_goto_cache[I]:
            return self._lr_goto_cache[I][x]

        s = self._lr_other_goto_cache.setdefault(x, IdentityDict())

        gs = []
        for p in I:
            n = p.lr_next
            if n and n.lr_before == x:
                s1 = s.get(n)
                if not s1:
                    s1 = {}
                    s[n] = s1
                gs.append(n)
                s = s1
        g = s.get("$end")
        if not g:
            if gs:
                g = self.lr0_closure(gs)
                s["$end"] = g
            else:
                s["$end"] = gs
        self._lr_goto_cache.setdefault(I, {})[x] = g
        return g

    def add_lalr_lookaheads(self, C):
        nullable = self.compute_nullable_nonterminals()
        trans = self.find_nonterminal_transitions(C)
        readsets = self.compute_read_sets(C, trans, nullable)
        lookd, included = self.compute_lookback_includes(C, trans, nullable)
        followsets = self.compute_follow_sets(trans, readsets, included)
        self.add_lookaheads(lookd, followsets)

    def compute_nullable_nonterminals(self):
        nullable = set()
        num_nullable = 0
        while True:
            for p in self.grammar.productions[1:]:
                if p.getlength() == 0:
                    nullable.add(p.name)
                    continue
                for t in p.prod:
                    if t not in nullable:
                        break
                else:
                    nullable.add(p.name)
            if len(nullable) == num_nullable:
                break
            num_nullable = len(nullable)
        return nullable

    def find_nonterminal_transitions(self, C):
        trans = []
        for idx, state in enumerate(C):
            for p in state:
                if p.lr_index < p.getlength() - 1:
                    t = (idx, p.prod[p.lr_index + 1])
                    if t[1] in self.grammar.nonterminals and t not in trans:
                        trans.append(t)
        return trans

    def compute_read_sets(self, C, ntrans, nullable):
        FP = lambda x: self.dr_relation(C, x, nullable)
        R = lambda x: self.reads_relation(C, x, nullable)
        return digraph(ntrans, R, FP)

    def compute_follow_sets(self, ntrans, readsets, includesets):
        FP = lambda x: readsets[x]
        R = lambda x: includesets.get(x, [])
        return digraph(ntrans, R, FP)

    def dr_relation(self, C, trans, nullable):
        state, N = trans
        terms = []

        g = self.lr0_goto(C[state], N)
        for p in g:
            if p.lr_index < p.getlength() - 1:
                a = p.prod[p.lr_index + 1]
                if a in self.grammar.terminals and a not in terms:
                    terms.append(a)
        if state == 0 and N == self.grammar.productions[0].prod[0]:
            terms.append("$end")
        return terms

    def reads_relation(self, C, trans, empty):
        rel = []
        state, N = trans

        g = self.lr0_goto(C[state], N)
        j = self.lr0_cidhash.get(g, -1)
        for p in g:
            if p.lr_index < p.getlength() - 1:
                a = p.prod[p.lr_index + 1]
                if a in empty:
                    rel.append((j, a))
        return rel

    def compute_lookback_includes(self, C, trans, nullable):
        lookdict = {}
        includedict = {}

        dtrans = dict.fromkeys(trans, 1)

        for state, N in trans:
            lookb = []
            includes = []
            for p in C[state]:
                if p.name != N:
                    continue

                lr_index = p.lr_index
                j = state
                while lr_index < p.getlength() - 1:
                    lr_index += 1
                    t = p.prod[lr_index]

                    if (j, t) in dtrans:
                        li = lr_index + 1
                        while li < p.getlength():
                            if p.prod[li] in self.grammar.terminals:
                                break
                            if p.prod[li] not in nullable:
                                break
                            li += 1
                        else:
                            includes.append((j, t))

                    g = self.lr0_goto(C[j], t)
                    j = self.lr0_cidhash.get(g, -1)

                for r in C[j]:
                    if r.name != p.name:
                        continue
                    if r.getlength() != p.getlength():
                        continue
                    i = 0
                    while i < r.lr_index:
                        if r.prod[i] != p.prod[i + 1]:
                            break
                        i += 1
                    else:
                        lookb.append((j, r))

            for i in includes:
                includedict.setdefault(i, []).append((state, N))
            lookdict[state, N] = lookb
        return lookdict, includedict

    def add_lookaheads(self, lookbacks, followset):
        for trans, lb in lookbacks.iteritems():
            for state, p in lb:
                if state not in p.lookaheads:
                    p.lookaheads[state] = []
                f = followset.get(trans, [])
                for a in f:
                    if a not in p.lookaheads[state]:
                        p.lookaheads[state].append(a)

    def build_table(self):
        C = self.lr0_items()

        self.add_lalr_lookaheads(C)

        st = 0
        for I in C:
            st_action = {}
            st_actionp = {}
            st_goto = {}
            for p in I:
                if p.getlength() == p.lr_index + 1:
                    if p.name == "S'":
                        # Start symbol. Accept!
                        st_action["$end"] = 0
                        st_actionp["$end"] = p
                    else:
                        laheads = p.lookaheads[st]
                        for a in laheads:
                            if a in st_action:
                                r = st_action[a]
                                if r > 0:
                                    sprec, slevel = self.grammar.productions[st_actionp[a].number].prec
                                    rprec, rlevel = self.grammar.precedence.get(a, ("right", 0))
                                    if (slevel < rlevel) or (slevel == rlevel and rprec == "left"):
                                        st_action[a] = -p.number
                                        st_actionp[a] = p
                                        if not slevel and not rlevel:
                                            self.sr_conflicts.append((st, a, "reduce"))
                                        self.grammar.productions[p.number].reduced += 1
                                    elif slevel == rlevel and rprec == "nonassoc":
                                        st_action[a] = None
                                    else:
                                        if not rlevel:
                                            self.sr_conflicts.append((st, a, "shift"))
                                elif r < 0:
                                    oldp = self.grammar.productions[-r]
                                    pp = self.grammar.productions[p.number]
                                    if oldp.number > pp.number:
                                        st_action[a] = -p.number
                                        st_actionp[a] = p
                                        chosenp, rejectp = pp, oldp
                                        self.grammar.productions[p.number].reduced += 1
                                        self.grammar.productions[oldp.number].reduced -= 1
                                    else:
                                        chosenp, rejectp = oldp, pp
                                    self.rr_conflicts.append((st, chosenp, rejectp))
                                else:
                                    raise LALRError("Unknown conflict in state %d" % st)
                            else:
                                st_action[a] = -p.number
                                st_actionp[a] = p
                                self.grammar.productions[p.number].reduced += 1
                else:
                    i = p.lr_index
                    a = p.prod[i + 1]
                    if a in self.grammar.terminals:
                        g = self.lr0_goto(I, a)
                        j = self.lr0_cidhash.get(g, -1)
                        if j >= 0:
                            if a in st_action:
                                r = st_action[a]
                                if r > 0:
                                    if r != j:
                                        raise LALRError("Shift/shift conflict in state %d" % st)
                                elif r < 0:
                                    rprec, rlevel = self.grammar.productions[st_actionp[a].number].prec
                                    sprec, slevel = self.grammar.precedence.get(a, ("right", 0))
                                    if (slevel > rlevel) or (slevel == rlevel and rprec == "right"):
                                        self.grammar.productions[st_actionp[a].number].reduced -= 1
                                        st_action[a] = j
                                        st_actionp[a] = p
                                        if not rlevel:
                                            self.sr_conflicts.append((st, a, "shift"))
                                    elif slevel == rlevel and rprec == "nonassoc":
                                        st_action[a] = None
                                    else:
                                        if not slevel and not rlevel:
                                            self.sr_conflicts.append((st, a, "reduce"))
                                else:
                                    raise LALRError("Unknown conflict in state %d" % st)
                            else:
                                st_action[a] = j
                                st_actionp[a] = p
            nkeys = set()
            for ii in I:
                for s in ii.unique_syms:
                    if s in self.grammar.nonterminals:
                        nkeys.add(s)
            for n in nkeys:
                g = self.lr0_goto(I, n)
                j = self.lr0_cidhash.get(g, -1)
                if j >= 0:
                    st_goto[n] = j

            self.lr_action[st] = st_action
            self.lr_goto[st] = st_goto
            st += 1
