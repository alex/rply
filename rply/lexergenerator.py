import re

try:
    import rpython
    from rpython.rlib.objectmodel import we_are_translated
    from rpython.rlib.rsre import rsre_core
    from rpython.rlib.rsre.rpy import get_code
except ImportError:
    rpython = None

    def we_are_translated():
        return False

from rply.lexer import Lexer


class Rule(object):
    _attrs_ = ['name', 'transition', 'target', 'flags', '_pattern']

    def __init__(self, name, pattern, flags=0, transition=None, target=None):
        self.name = name
        self.re = re.compile(pattern, flags=flags)
        self.transition = transition
        self.target = target
        if rpython:
            self.flags = flags
            self._pattern = get_code(pattern, flags)

    def _freeze_(self):
        return True

    def matches(self, s, pos):
        if not we_are_translated():
            m = self.re.match(s, pos)
            return Match(*m.span(0)) if m is not None else None
        else:
            assert pos >= 0
            ctx = rsre_core.StrMatchContext(s, pos, len(s), self.flags)

            matched = rsre_core.match_context(ctx, self._pattern)
            if matched:
                return Match(ctx.match_start, ctx.match_end)
            else:
                return None


class Match(object):
    _attrs_ = ["start", "end"]

    def __init__(self, start, end):
        self.start = start
        self.end = end


class LexerState(object):
    def __init__(self):
        self.rules = []
        self.ignore_rules = []

    def add(self, name, pattern, flags=0, transition=None, target=None):
        self.rules.append(Rule(name, pattern, flags, transition, target))

    def ignore(self, pattern, flags=0, transition=None, target=None):
        self.ignore_rules.append(Rule('', pattern, flags, transition, target))


class LexerGenerator(object):
    r"""
    A LexerGenerator represents a set of rules that match pieces of text that
    should either be turned into tokens or ignored by the lexer.

    Rules are added using the :meth:`add` and :meth:`ignore` methods:
    A LexerGenerator represents a set of state objects, each state consists of
    a set of rules that match pieces of text that should either be turned into
    tokens or ignored by the lexer. For convenience an initial state with the
    name passed as `initial_state` is created for you, to which you can add
    rules using the :meth:`add` and :meth:`ignore` methods:

    >>> from rply import LexerGenerator
    >>> lg = LexerGenerator()
    >>> lg.add('NUMBER', r'\d+')
    >>> lg.add('ADD', r'\+')
    >>> lg.ignore(r'\s+')

    The rules are passed to :func:`re.compile`. If you need additional flags,
    e.g. :const:`re.DOTALL`, you can pass them to :meth:`add` and
    :meth:`ignore` as an additional optional parameter:

    >>> import re
    >>> lg.add('ALL', r'.*', flags=re.DOTALL)

    You can then build a lexer with which you can lex a string to produce an
    iterator yielding tokens:

    >>> lexer = lg.build()
    >>> iterator = lexer.lex('1 + 1')
    >>> iterator.next()
    Token('NUMBER', '1')
    >>> iterator.next()
    Token('ADD', '+')
    >>> iterator.next()
    Token('NUMBER', '1')
    >>> iterator.next()
    Traceback (most recent call last):
    ...
    StopIteration
    """
    def __init__(self, initial_state='start'):
        self.initial_state = initial_state

        self.states = {initial_state: LexerState()}

    def add(self, *args, **kwargs):
        """
        Adds a rule with the given `name` and `pattern`. In case of ambiguity,
        the first rule added wins.

        If you want the state of the parser to change after this rule has
        matched, you can perform a transition by passing ``"push"`` or
        ``"pop"``, to either push a state to the stack of states or to pop a
        state from that stack. If you do push a state to the stack, you need
        to pass the name of that state as `target`.
        """
        self.states[self.initial_state].add(*args, **kwargs)

    def ignore(self, *args, **kwargs):
        """
        Adds a rule whose matched value will be ignored. Ignored rules will be
        matched before regular ones.

        See :meth:`add` on the `transition` and `target` argument.
        """
        self.states[self.initial_state].ignore(*args, **kwargs)

    def build(self):
        """
        Returns a lexer instance, which provides a `lex` method that must be
        called with a string and returns an iterator yielding
        :class:`~rply.Token` instances.
        """
        return Lexer(self.states[self.initial_state], self.states)

    def add_state(self, name):
        """
        Adds a state with the given `name` and returns it. The returned state
        has `add` and `ignore` methods equivalent to :meth:`add` and
        :meth:`ignore`.
        """
        state = self.states[name] = LexerState()
        return state


if rpython:
    class RuleEntry(ExtRegistryEntry):
        _type_ = Rule

        def compute_annotation(self, *args):
            return SomeRule()

    class SomeRule(model.SomeObject):
        def rtyper_makekey(self):
            return (type(self),)

        def rtyper_makerepr(self, rtyper):
            return RuleRepr(rtyper)

        def method_matches(self, s_s, s_pos):
            assert model.SomeString().contains(s_s)
            assert model.SomeInteger(nonneg=True).contains(s_pos)

            bk = getbookkeeper()
            init_pbc = bk.immutablevalue(Match.__init__)
            bk.emulate_pbc_call((self, "match_init"), init_pbc, [
                model.SomeInstance(bk.getuniqueclassdef(Match)),
                model.SomeInteger(nonneg=True),
                model.SomeInteger(nonneg=True)
            ])
            init_pbc = bk.immutablevalue(rsre_core.StrMatchContext.__init__)
            bk.emulate_pbc_call((self, "str_match_context_init"), init_pbc, [
                model.SomeInstance(bk.getuniqueclassdef(rsre_core.StrMatchContext)),
                bk.newlist(model.SomeInteger(nonneg=True)),
                model.SomeString(),
                model.SomeInteger(nonneg=True),
                model.SomeInteger(nonneg=True),
                model.SomeInteger(nonneg=True),
            ])
            match_context_pbc = bk.immutablevalue(rsre_core.match_context)
            bk.emulate_pbc_call((self, "match_context"), match_context_pbc, [
                model.SomeInstance(bk.getuniqueclassdef(rsre_core.StrMatchContext)),
            ])

            return model.SomeInstance(getbookkeeper().getuniqueclassdef(Match), can_be_None=True)

        def getattr(self, s_attr):
            if s_attr.is_constant() and s_attr.const in ["name", "transition", "target"]:
                return model.SomeString()
            return super(SomeRule, self).getattr(s_attr)

    class __extend__(pairtype(SomeRule, SomeRule)):
        def union(self):
            return SomeRule()

    class RuleRepr(Repr):
        def __init__(self, rtyper):
            super(RuleRepr, self).__init__()

            self.ll_rule_cache = {}

            self.match_init_repr = rtyper.getrepr(
                rtyper.annotator.bookkeeper.immutablevalue(Match.__init__)
            )
            self.match_context_init_repr = rtyper.getrepr(
                rtyper.annotator.bookkeeper.immutablevalue(rsre_core.StrMatchContext.__init__)
            )
            self.match_context_repr = rtyper.getrepr(
                rtyper.annotator.bookkeeper.immutablevalue(rsre_core.match_context)
            )

            list_repr = FixedSizeListRepr(rtyper, rtyper.getrepr(model.SomeInteger(nonneg=True)))
            list_repr._setup_repr()
            self.lowleveltype = lltype.Ptr(lltype.GcStruct(
                "RULE",
                ("name", lltype.Ptr(STR)),
                ("transition", lltype.Ptr(STR)),
                ("target", lltype.Ptr(STR)),
                ("code", list_repr.lowleveltype),
            ))

        def convert_const(self, rule):
            if rule not in self.ll_rule_cache:
                ll_rule = lltype.malloc(self.lowleveltype.TO)
                ll_rule.name = llstr(rule.name)
                ll_rule.transition = llstr(rule.transition)
                ll_rule.target = llstr(rule.target)
                code = get_code(rule.re.pattern)
                ll_rule.code = lltype.malloc(self.lowleveltype.TO.code.TO, len(code))
                for i, c in enumerate(code):
                    ll_rule.code[i] = c
                self.ll_rule_cache[rule] = ll_rule
            return self.ll_rule_cache[rule]

        def rtype_getattr(self, hop):
            s_attr = hop.args_s[1]
            if s_attr.is_constant() and s_attr.const == "name":
                v_rule = hop.inputarg(self, arg=0)
                return hop.gendirectcall(LLRule.ll_get_name, v_rule)
            elif s_attr.is_constant() and s_attr.const == "transition":
                v_rule = hop.inputarg(self, arg=0)
                return hop.gendirectcall(LLRule.ll_get_transition, v_rule)
            elif s_attr.is_constant() and s_attr.const == "target":
                v_rule = hop.inputarg(self, arg=0)
                return hop.gendirectcall(LLRule.ll_get_target, v_rule)
            return super(RuleRepr, self).rtype_getattr(hop)

        def rtype_method_matches(self, hop):
            [v_rule, v_s, v_pos] = hop.inputargs(self, string_repr, lltype.Signed)
            c_MATCHTYPE = hop.inputconst(lltype.Void, Match)
            c_MATCH_INIT = hop.inputconst(lltype.Void, self.match_init_repr)
            c_MATCH_CONTEXTTYPE = hop.inputconst(lltype.Void, rsre_core.StrMatchContext)
            c_MATCH_CONTEXT_INIT = hop.inputconst(lltype.Void, self.match_context_init_repr)
            c_MATCH_CONTEXT = hop.inputconst(lltype.Void, self.match_context_repr)

            return hop.gendirectcall(
                LLRule.ll_matches,
                c_MATCHTYPE, c_MATCH_INIT, c_MATCH_CONTEXTTYPE,
                c_MATCH_CONTEXT_INIT, c_MATCH_CONTEXT, v_rule, v_s, v_pos
            )

    class LLRule(object):
        @staticmethod
        def ll_get_name(ll_rule):
            return ll_rule.name

        @staticmethod
        def ll_get_transition(ll_rule):
            return ll_rule.transition

        @staticmethod
        def ll_get_target(ll_rule):
            return ll_rule.target

        @staticmethod
        def ll_matches(MATCHTYPE, MATCH_INIT, MATCH_CONTEXTTYPE,
                       MATCH_CONTEXT_INIT, MATCH_CONTEXT, ll_rule, s, pos):
            s = hlstr(s)
            assert pos >= 0
            ctx = instantiate(MATCH_CONTEXTTYPE)
            hlinvoke(
                MATCH_CONTEXT_INIT, rsre_core.StrMatchContext.__init__,
                ctx, ll_rule.code, hlstr(s), pos, len(s), 0
            )
            matched = hlinvoke(MATCH_CONTEXT, rsre_core.match_context, ctx)
            if matched:
                match = instantiate(MATCHTYPE)
                hlinvoke(
                    MATCH_INIT, Match.__init__,
                    match, ctx.match_start, ctx.match_end
                )
                return match
            else:
                return None
