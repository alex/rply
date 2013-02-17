import re

try:
    import rpython
    from rpython.annotator import model
    from rpython.annotator.bookkeeper import getbookkeeper
    from rpython.rlib.rsre import rsre_core
    from rpython.rlib.rsre.rpy import get_code
    from rpython.rtyper.annlowlevel import llstr, hlstr
    from rpython.rtyper.extregistry import ExtRegistryEntry
    from rpython.rtyper.lltypesystem import lltype
    from rpython.rtyper.lltypesystem.rstr import STR, string_repr
    from rpython.rtyper.rmodel import Repr
    from rpython.tool.pairtype import pairtype
except ImportError:
    rpython = None

from rply.lexer import Lexer


class Rule(object):
    def __init__(self, name, pattern):
        self.name = name
        self.re = re.compile(pattern)

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
    def __init__(self):
        self.rules = []

    def add(self, name, pattern):
        self.rules.append(Rule(name, pattern))

    def build(self):
        return Lexer(self.rules)

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
            assert model.SomeInteger().contains(s_pos)

            bk = getbookkeeper()
            init_pbc = bk.immutablevalue(Match.__init__)
            bk.emulate_pbc_call((self, "match_init"), init_pbc, [
                model.SomeInstance(bk.getuniqueclassdef(Match)),
                model.SomeInteger(nonneg=True),
                model.SomeInteger(nonneg=True)
            ])
            return model.SomeInstance(getbookkeeper().getuniqueclassdef(Match), can_be_None=True)

        def getattr(self, s_attr):
            if s_attr.is_constant() and s_attr.const == "name":
                return model.SomeString()
            return super(SomeRule, self).getattr(s_attr)

    class __extend__(pairtype(SomeRule, SomeRule)):
        def union((self, other)):
            return self

    class RuleRepr(Repr):
        def __init__(self, rtyper):
            super(RuleRepr, self).__init__()
            self.lowleveltype = lltype.Ptr(lltype.GcStruct("RULE",
                ("name", lltype.Ptr(STR)),
                ("code", lltype.Ptr(lltype.GcArray(lltype.Signed))),
            ))

        def convert_const(self, rule):
            ll_rule = lltype.malloc(self.lowleveltype.TO)
            ll_rule.name = llstr(rule.name)
            code = get_code(rule.re.pattern)
            ll_rule.code = lltype.malloc(self.lowleveltype.TO.code.TO, len(code))
            for i, c in enumerate(code):
                ll_rule.code[i] = c
            return ll_rule

        def rtype_getattr(self, hop):
            s_attr = hop.args_s[1]
            if s_attr.is_constant() and s_attr.const == "name":
                v_rule = hop.inputarg(self, arg=0)
                return hop.gendirectcall(LLRule.ll_get_name, v_rule)
            return super(RuleRepr, self).rtype_getattr(hop)

        def rtype_method_matches(self, hop):
            [v_rule, v_s, v_pos] = hop.inputargs(self, string_repr, lltype.Signed)
            return hop.gendirectcall(LLRule.ll_matches, v_rule, v_s, v_pos)

    class LLRule(object):
        @staticmethod
        def ll_get_name(ll_rule):
            return ll_rule.name

        @staticmethod
        def ll_matches(ll_rule, s, pos):
            s = hlstr(s)
            ctx = rsre_core.StrMatchContext(ll_rule.code, hlstr(s), pos, len(s), 0)
            matched = rsre_core.search_context(ctx)
            if matched:
                raise NotImplementedError
            else:
                return lltype.nullptr()
