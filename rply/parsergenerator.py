import errno
import hashlib
import json
import os
import sys
import tempfile
import warnings

from appdirs import AppDirs

from rply.errors import ParserGeneratorError, ParserGeneratorWarning
from rply.grammar import Grammar
from rply.parser import LRParser
from rply.utils import Counter, IdentityDict, iteritems, itervalues


LARGE_VALUE = sys.maxsize


class ParserGenerator(object):
    """
    A ParserGenerator represents a set of production rules, that define a
    sequence of terminals and non-terminals to be replaced with a non-terminal,
    which can be turned into a parser.

    :param tokens: A list of token (non-terminal) names.
    :param precedence: A list of tuples defining the order of operation for
                       avoiding ambiguity, consisting of a string defining
                       associativity (left, right or nonassoc) and a list of
                       token names with the same associativity and level of
                       precedence.
    :param cache_id: A string specifying an ID for caching.
    """
    VERSION = 1

    def __init__(self, tokens, precedence=[], cache_id=None):
        self.tokens = tokens
        self.productions = []
        self.precedence = precedence
        self.cache_id = cache_id
        self.error_handler = None

    def production(self, rule, precedence=None):
        """
        A decorator that defines one or many production rules and registers
        the decorated function to be called with the terminals and
        non-terminals matched by those rules.

        A `rule` should consist of a name defining the non-terminal returned
        by the decorated function and one or more sequences of pipe-separated
        non-terminals and terminals that are supposed to be replaced::

            replacing_non_terminal : TERMINAL1 non_term1 | TERMINAL2 non_term2

        The name of the non-terminal replacing the sequence is on the left,
        separated from the sequence by a colon. The whitespace around the colon
        is required.

        Knowing this we can define productions::

            pg = ParserGenerator(['NUMBER', 'ADD'])

            @pg.production('number : NUMBER')
            def expr_number(p):
                return BoxInt(int(p[0].getstr()))

            @pg.production('expr : number ADD number')
            def expr_add(p):
                return BoxInt(p[0].getint() + p[2].getint())

        If a state was passed to the parser, the decorated function is
        additionally called with that state as first argument.
        """
        parts = rule.split()
        production_name = parts[0]
        if parts[1] != ":":
            raise ParserGeneratorError("Expecting :")

        body = " ".join(parts[2:])
        prods = body.split("|")

        def inner(func):
            for production in prods:
                syms = production.split()
                self.productions.append((production_name, syms, func, precedence))
            return func
        return inner

    def error(self, func):
        """
        Sets the error handler that is called with the state (if passed to the
        parser) and the token the parser errored on.

        Currently error handlers must raise an exception. If an error handler
        is not defined, a :exc:`rply.ParsingError` will be raised.
        """
        self.error_handler = func
        return func

    def compute_grammar_hash(self, g):
        hasher = hashlib.sha1()
        hasher.update(g.start.encode())
        hasher.update(json.dumps(sorted(g.terminals)).encode())
        for term, (assoc, level) in sorted(iteritems(g.precedence)):
            hasher.update(term.encode())
            hasher.update(assoc.encode())
            hasher.update(bytes(level))
        for p in g.productions:
            hasher.update(p.name.encode())
            hasher.update(json.dumps(p.prec).encode())
            hasher.update(json.dumps(p.prod).encode())
        return hasher.hexdigest()

    def serialize_table(self, table):
        return {
            "lr_action": table.lr_action,
            "lr_goto": table.lr_goto,
            "sr_conflicts": table.sr_conflicts,
            "rr_conflicts": table.rr_conflicts,
            "default_reductions": table.default_reductions,
            "start": table.grammar.start,
            "terminals": sorted(table.grammar.terminals),
            "precedence": table.grammar.precedence,
            "productions": [
                (p.name, p.prod, p.prec) for p in table.grammar.productions
            ],
        }

    def data_is_valid(self, g, data):
        if g.start != data["start"]:
            return False
        if sorted(g.terminals) != data["terminals"]:
            return False
        if sorted(g.precedence) != sorted(data["precedence"]):
            return False
        for key, (assoc, level) in iteritems(g.precedence):
            if data["precedence"][key] != [assoc, level]:
                return False
        if len(g.productions) != len(data["productions"]):
            return False
        for p, (name, prod, (assoc, level)) in zip(g.productions, data["productions"]):
            if p.name != name:
                return False
            if p.prod != prod:
                return False
            if p.prec != (assoc, level):
                return False
        return True

    def build(self):
        g = Grammar(self.tokens)

        for level, (assoc, terms) in enumerate(self.precedence, 1):
            for term in terms:
                g.set_precedence(term, assoc, level)

        for prod_name, syms, func, precedence in self.productions:
            g.add_production(prod_name, syms, func, precedence)

        g.set_start()

        for unused_term in g.unused_terminals():
            warnings.warn(
                "Token %r is unused" % unused_term,
                ParserGeneratorWarning,
                stacklevel=2
            )
        for unused_prod in g.unused_productions():
            warnings.warn(
                "Production %r is not reachable" % unused_prod,
                ParserGeneratorWarning,
                stacklevel=2
            )

        g.build_lritems()
        g.compute_first()
        g.compute_follow()

        table = None
        if self.cache_id is not None:
            cache_dir = AppDirs("rply").user_cache_dir
            cache_file = os.path.join(
                cache_dir,
                "%s-%s-%s.json" % (
                    self.cache_id, self.VERSION, self.compute_grammar_hash(g)
                )
            )

            if os.path.exists(cache_file):
                with open(cache_file) as f:
                    data = json.load(f)
                if self.data_is_valid(g, data):
                    table = LRTable.from_cache(g, data)
        if table is None:
            table = LRTable.from_grammar(g)

            if self.cache_id is not None:
                self._write_cache(cache_dir, cache_file, table)

        if table.sr_conflicts:
            warnings.warn(
                "%d shift/reduce conflict%s" % (
                    len(table.sr_conflicts),
                    "s" if len(table.sr_conflicts) > 1 else ""
                ),
                ParserGeneratorWarning,
                stacklevel=2,
            )
        if table.rr_conflicts:
            warnings.warn(
                "%d reduce/reduce conflict%s" % (
                    len(table.rr_conflicts),
                    "s" if len(table.rr_conflicts) > 1 else ""
                ),
                ParserGeneratorWarning,
                stacklevel=2,
            )
        return LRParser(table, self.error_handler)

    def _write_cache(self, cache_dir, cache_file, table):
        if not os.path.exists(cache_dir):
            try:
                os.makedirs(cache_dir, mode=0o0700)
            except OSError as e:
                if e.errno == errno.EROFS:
                    return
                raise

        with tempfile.NamedTemporaryFile(dir=cache_dir, delete=False, mode="w") as f:
            json.dump(self.serialize_table(table), f)
        os.rename(f.name, cache_file)


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
        N[stack[-1]] = LARGE_VALUE
        F[stack[-1]] = F[x]
        element = stack.pop()
        while element != x:
            N[stack[-1]] = LARGE_VALUE
            F[stack[-1]] = F[x]
            element = stack.pop()


class LRTable(object):
    def __init__(self, grammar, lr_action, lr_goto, default_reductions,
                 sr_conflicts, rr_conflicts):
        self.grammar = grammar
        self.lr_action = lr_action
        self.lr_goto = lr_goto
        self.default_reductions = default_reductions
        self.sr_conflicts = sr_conflicts
        self.rr_conflicts = rr_conflicts

    @classmethod
    def from_cache(cls, grammar, data):
        lr_action = [
            dict([(str(k), v) for k, v in iteritems(action)])
            for action in data["lr_action"]
        ]
        lr_goto = [
            dict([(str(k), v) for k, v in iteritems(goto)])
            for goto in data["lr_goto"]
        ]
        return LRTable(
            grammar,
            lr_action,
            lr_goto,
            data["default_reductions"],
            data["sr_conflicts"],
            data["rr_conflicts"]
        )

    @classmethod
    def from_grammar(cls, grammar):
        cidhash = IdentityDict()
        goto_cache = {}
        add_count = Counter()
        C = cls.lr0_items(grammar, add_count, cidhash, goto_cache)

        cls.add_lalr_lookaheads(grammar, C, add_count, cidhash, goto_cache)

        lr_action = [None] * len(C)
        lr_goto = [None] * len(C)
        sr_conflicts = []
        rr_conflicts = []
        for st, I in enumerate(C):
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
                                    sprec, slevel = grammar.productions[st_actionp[a].number].prec
                                    rprec, rlevel = grammar.precedence.get(a, ("right", 0))
                                    if (slevel < rlevel) or (slevel == rlevel and rprec == "left"):
                                        st_action[a] = -p.number
                                        st_actionp[a] = p
                                        if not slevel and not rlevel:
                                            sr_conflicts.append((st, repr(a), "reduce"))
                                        grammar.productions[p.number].reduced += 1
                                    elif not (slevel == rlevel and rprec == "nonassoc"):
                                        if not rlevel:
                                            sr_conflicts.append((st, repr(a), "shift"))
                                elif r < 0:
                                    oldp = grammar.productions[-r]
                                    pp = grammar.productions[p.number]
                                    if oldp.number > pp.number:
                                        st_action[a] = -p.number
                                        st_actionp[a] = p
                                        chosenp, rejectp = pp, oldp
                                        grammar.productions[p.number].reduced += 1
                                        grammar.productions[oldp.number].reduced -= 1
                                    else:
                                        chosenp, rejectp = oldp, pp
                                    rr_conflicts.append((st, repr(chosenp), repr(rejectp)))
                                else:
                                    raise ParserGeneratorError("Unknown conflict in state %d" % st)
                            else:
                                st_action[a] = -p.number
                                st_actionp[a] = p
                                grammar.productions[p.number].reduced += 1
                else:
                    i = p.lr_index
                    a = p.prod[i + 1]
                    if a in grammar.terminals:
                        g = cls.lr0_goto(I, a, add_count, goto_cache)
                        j = cidhash.get(g, -1)
                        if j >= 0:
                            if a in st_action:
                                r = st_action[a]
                                if r > 0:
                                    if r != j:
                                        raise ParserGeneratorError("Shift/shift conflict in state %d" % st)
                                elif r < 0:
                                    rprec, rlevel = grammar.productions[st_actionp[a].number].prec
                                    sprec, slevel = grammar.precedence.get(a, ("right", 0))
                                    if (slevel > rlevel) or (slevel == rlevel and rprec == "right"):
                                        grammar.productions[st_actionp[a].number].reduced -= 1
                                        st_action[a] = j
                                        st_actionp[a] = p
                                        if not rlevel:
                                            sr_conflicts.append((st, repr(a), "shift"))
                                    elif not (slevel == rlevel and rprec == "nonassoc"):
                                        if not slevel and not rlevel:
                                            sr_conflicts.append((st, repr(a), "reduce"))
                                else:
                                    raise ParserGeneratorError("Unknown conflict in state %d" % st)
                            else:
                                st_action[a] = j
                                st_actionp[a] = p
            nkeys = set()
            for ii in I:
                for s in ii.unique_syms:
                    if s in grammar.nonterminals:
                        nkeys.add(s)
            for n in nkeys:
                g = cls.lr0_goto(I, n, add_count, goto_cache)
                j = cidhash.get(g, -1)
                if j >= 0:
                    st_goto[n] = j

            lr_action[st] = st_action
            lr_goto[st] = st_goto

        default_reductions = [0] * len(lr_action)
        for state, actions in enumerate(lr_action):
            actions = set(itervalues(actions))
            if len(actions) == 1 and next(iter(actions)) < 0:
                default_reductions[state] = next(iter(actions))
        return LRTable(grammar, lr_action, lr_goto, default_reductions, sr_conflicts, rr_conflicts)

    @classmethod
    def lr0_items(cls, grammar, add_count, cidhash, goto_cache):
        C = [cls.lr0_closure([grammar.productions[0].lr_next], add_count)]
        for i, I in enumerate(C):
            cidhash[I] = i

        i = 0
        while i < len(C):
            I = C[i]
            i += 1

            asyms = set()
            for ii in I:
                asyms.update(ii.unique_syms)
            for x in asyms:
                g = cls.lr0_goto(I, x, add_count, goto_cache)
                if not g:
                    continue
                if g in cidhash:
                    continue
                cidhash[g] = len(C)
                C.append(g)
        return C

    @classmethod
    def lr0_closure(cls, I, add_count):
        add_count.incr()

        J = I[:]
        added = True
        while added:
            added = False
            for j in J:
                for x in j.lr_after:
                    if x.lr0_added == add_count.value:
                        continue
                    J.append(x.lr_next)
                    x.lr0_added = add_count.value
                    added = True
        return J

    @classmethod
    def lr0_goto(cls, I, x, add_count, goto_cache):
        s = goto_cache.setdefault(x, IdentityDict())

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
                g = cls.lr0_closure(gs, add_count)
                s["$end"] = g
            else:
                s["$end"] = gs
        return g

    @classmethod
    def add_lalr_lookaheads(cls, grammar, C, add_count, cidhash, goto_cache):
        nullable = cls.compute_nullable_nonterminals(grammar)
        trans = cls.find_nonterminal_transitions(grammar, C)
        readsets = cls.compute_read_sets(grammar, C, trans, nullable, add_count, cidhash, goto_cache)
        lookd, included = cls.compute_lookback_includes(grammar, C, trans, nullable, add_count, cidhash, goto_cache)
        followsets = cls.compute_follow_sets(trans, readsets, included)
        cls.add_lookaheads(lookd, followsets)

    @classmethod
    def compute_nullable_nonterminals(cls, grammar):
        nullable = set()
        num_nullable = 0
        while True:
            for p in grammar.productions[1:]:
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

    @classmethod
    def find_nonterminal_transitions(cls, grammar, C):
        trans = []
        for idx, state in enumerate(C):
            for p in state:
                if p.lr_index < p.getlength() - 1:
                    t = (idx, p.prod[p.lr_index + 1])
                    if t[1] in grammar.nonterminals and t not in trans:
                        trans.append(t)
        return trans

    @classmethod
    def compute_read_sets(cls, grammar, C, ntrans, nullable, add_count, cidhash, goto_cache):
        return digraph(
            ntrans,
            R=lambda x: cls.reads_relation(C, x, nullable, add_count, cidhash, goto_cache),
            FP=lambda x: cls.dr_relation(grammar, C, x, nullable, add_count, goto_cache)
        )

    @classmethod
    def compute_follow_sets(cls, ntrans, readsets, includesets):
        return digraph(
            ntrans,
            R=lambda x: includesets.get(x, []),
            FP=lambda x: readsets[x],
        )

    @classmethod
    def dr_relation(cls, grammar, C, trans, nullable, add_count, goto_cache):
        state, N = trans
        terms = []

        g = cls.lr0_goto(C[state], N, add_count, goto_cache)
        for p in g:
            if p.lr_index < p.getlength() - 1:
                a = p.prod[p.lr_index + 1]
                if a in grammar.terminals and a not in terms:
                    terms.append(a)
        if state == 0 and N == grammar.productions[0].prod[0]:
            terms.append("$end")
        return terms

    @classmethod
    def reads_relation(cls, C, trans, empty, add_count, cidhash, goto_cache):
        rel = []
        state, N = trans

        g = cls.lr0_goto(C[state], N, add_count, goto_cache)
        j = cidhash.get(g, -1)
        for p in g:
            if p.lr_index < p.getlength() - 1:
                a = p.prod[p.lr_index + 1]
                if a in empty:
                    rel.append((j, a))
        return rel

    @classmethod
    def compute_lookback_includes(cls, grammar, C, trans, nullable, add_count, cidhash, goto_cache):
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
                            if p.prod[li] in grammar.terminals:
                                break
                            if p.prod[li] not in nullable:
                                break
                            li += 1
                        else:
                            includes.append((j, t))

                    g = cls.lr0_goto(C[j], t, add_count, goto_cache)
                    j = cidhash.get(g, -1)

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

    @classmethod
    def add_lookaheads(cls, lookbacks, followset):
        for trans, lb in iteritems(lookbacks):
            for state, p in lb:
                f = followset.get(trans, [])
                laheads = p.lookaheads.setdefault(state, [])
                for a in f:
                    if a not in laheads:
                        laheads.append(a)
