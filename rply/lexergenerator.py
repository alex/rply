import re

try:
    import rpython
    from rpython.annotator import model
    from rpython.annotator.bookkeeper import getbookkeeper
    from rpython.rlib.objectmodel import instantiate, hlinvoke
    from rpython.rlib.rsre import rsre_core
    from rpython.rlib.rsre.rpy import get_code
    from rpython.rtyper.annlowlevel import llstr, hlstr
    from rpython.rtyper.extregistry import ExtRegistryEntry
    from rpython.rtyper.lltypesystem import lltype
    from rpython.rtyper.lltypesystem.rlist import FixedSizeListRepr
    from rpython.rtyper.lltypesystem.rstr import STR, string_repr
    from rpython.rtyper.rmodel import Repr
    from rpython.tool.pairtype import pairtype
except ImportError:
    rpython = None

from rply.lexer import Lexer


class Rule(object):
    def __init__(self, name, pattern, flags=0):
        self.name = name
        self.re = re.compile(pattern, flags=flags)

    def _freeze_(self):
        return True

    def matches(self, s, pos):
        m = self.re.match(s, pos)
        return Match(*m.span(0)) if m is not None else None


class Match(object):
    _attrs_ = ["start", "end"]

    def __init__(self, start, end):
        self.start = start
        self.end = end


class LexerGenerator(object):
    """
    A LexerGenerator represents a set of rules that match pieces of text that
    should either be turned into tokens or ignored by the lexer.

    Rules are added using the :meth:`add` and :meth:`ignore` methods:

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

    def __init__(self):
        self.rules = []
        self.ignore_rules = []

    def add(self, name, pattern, flags=0):
        """
        Adds a rule with the given `name` and `pattern`. In case of ambiguity,
        the first rule added wins.
        """
        self.rules.append(Rule(name, pattern, flags=flags))

    def ignore(self, pattern, flags=0):
        """
        Adds a rule whose matched value will be ignored. Ignored rules will be
        matched before regular ones.
        """
        self.ignore_rules.append(Rule("", pattern, flags=flags))

    def build(self):
        """
        Returns a lexer instance, which provides a `lex` method that must be
        called with a string and returns an iterator yielding
        :class:`~rply.Token` instances.
        """
        return Lexer(self.rules, self.ignore_rules)

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
                model.SomeInstance(
                    bk.getuniqueclassdef(rsre_core.StrMatchContext)
                ),
                bk.newlist(model.SomeInteger(nonneg=True)),
                model.SomeString(),
                model.SomeInteger(nonneg=True),
                model.SomeInteger(nonneg=True),
                model.SomeInteger(nonneg=True),
            ])
            match_context_pbc = bk.immutablevalue(rsre_core.match_context)
            bk.emulate_pbc_call((self, "match_context"), match_context_pbc, [
                model.SomeInstance(
                    bk.getuniqueclassdef(rsre_core.StrMatchContext)
                ),
            ])

            return model.SomeInstance(
                getbookkeeper().getuniqueclassdef(Match), can_be_None=True
            )

        def getattr(self, s_attr):
            if s_attr.is_constant() and s_attr.const == "name":
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
                rtyper.annotator.bookkeeper.immutablevalue(
                    rsre_core.StrMatchContext.__init__
                )
            )
            self.match_context_repr = rtyper.getrepr(
                rtyper.annotator.bookkeeper.immutablevalue(
                    rsre_core.match_context
                )
            )

            list_repr = FixedSizeListRepr(
                rtyper, rtyper.getrepr(model.SomeInteger(nonneg=True))
            )
            list_repr._setup_repr()
            self.lowleveltype = lltype.Ptr(lltype.GcStruct(
                "RULE",
                ("name", lltype.Ptr(STR)),
                ("code", list_repr.lowleveltype),
                ("flags", lltype.Signed),
            ))

        def convert_const(self, rule):
            if rule not in self.ll_rule_cache:
                ll_rule = lltype.malloc(self.lowleveltype.TO)
                ll_rule.name = llstr(rule.name)
                code = get_code(rule.re.pattern)
                ll_rule.code = lltype.malloc(
                    self.lowleveltype.TO.code.TO, len(code)
                )
                for i, c in enumerate(code):
                    ll_rule.code[i] = c
                ll_rule.flags = rule.re.flags
                self.ll_rule_cache[rule] = ll_rule
            return self.ll_rule_cache[rule]

        def rtype_getattr(self, hop):
            s_attr = hop.args_s[1]
            if s_attr.is_constant() and s_attr.const == "name":
                v_rule = hop.inputarg(self, arg=0)
                return hop.gendirectcall(LLRule.ll_get_name, v_rule)
            return super(RuleRepr, self).rtype_getattr(hop)

        def rtype_method_matches(self, hop):
            [v_rule, v_s, v_pos] = hop.inputargs(
                self, string_repr, lltype.Signed
            )
            c_MATCHTYPE = hop.inputconst(lltype.Void, Match)
            c_MATCH_INIT = hop.inputconst(
                lltype.Void, self.match_init_repr
            )
            c_MATCH_CONTEXTTYPE = hop.inputconst(
                lltype.Void, rsre_core.StrMatchContext
            )
            c_MATCH_CONTEXT_INIT = hop.inputconst(
                lltype.Void, self.match_context_init_repr
            )
            c_MATCH_CONTEXT = hop.inputconst(
                lltype.Void, self.match_context_repr
            )

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
        def ll_matches(MATCHTYPE, MATCH_INIT, MATCH_CONTEXTTYPE,
                       MATCH_CONTEXT_INIT, MATCH_CONTEXT, ll_rule, s, pos):
            s = hlstr(s)
            assert pos >= 0
            ctx = instantiate(MATCH_CONTEXTTYPE)
            hlinvoke(
                MATCH_CONTEXT_INIT, rsre_core.StrMatchContext.__init__,
                ctx, ll_rule.code, hlstr(s), pos, len(s), ll_rule.flags
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
