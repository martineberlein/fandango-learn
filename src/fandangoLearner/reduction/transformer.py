from typing import Dict, List

from fandango.language.grammar import NodeVisitor, Concatenation, Node, TerminalNode, NonTerminalNode, Alternative, \
    Option, Star, Repetition, Plus, CharSet


class ExpansionNameVisitor(NodeVisitor):

    def visitTerminalNode(self, node: TerminalNode):
        return str(node.symbol)


class DerivableCharsetVisitor(NodeVisitor):

    def aggregate_results(self, aggregate, result):
        return aggregate.union(result)

    def default_result(self):
        return set()

    def visitTerminalNode(self, node: TerminalNode):
        return str(node.symbol)


class NonTerminalVisitor(NodeVisitor):

    def aggregate_results(self, aggregate, result):
        return aggregate.union(result)

    def default_result(self):
        return set()

    def visitNonTerminalNode(self, node: TerminalNode):
        return {node.symbol}


class CleanNameVisitor(NodeVisitor):
    """
    Utility visitor that returns just the string form
    of a Terminal or NonTerminal symbol.
    """
    def visitTerminalNode(self, node: TerminalNode):
        return str(node.symbol)

    def visitNonTerminalNode(self, node: NonTerminalNode):
        # Fuzzingbook typically encloses nonterminals in <...>
        # Make sure node.symbol already has < > or add them if needed
        name = str(node.symbol)
        if not (name.startswith("<") and name.endswith(">")):
            name = f"<{name}>"
        return name

    # For everything else, just do nothing special
    def visitAlternative(self, node: Alternative):
        return None

    def visitConcatenation(self, node: Concatenation):
        return None

    def visitOption(self, node: Option):
        return None

    def visitStar(self, node: Star):
        return None

    def visitRepetition(self, node: Repetition):
        return None

    def visitPlus(self, node: Plus):
        return None

    def visitCharSet(self, node: CharSet):
        return None


class NameGrammarVisitor(NodeVisitor):
    """
    Transforms a Fandango grammar into a Fuzzingbook-style grammar,
    introducing new nonterminals for Star, Plus, etc.
    """

    def __init__(self):
        self.grammar_: Dict[str, List[str]] = {}
        self.clean_names = CleanNameVisitor()
        # A cache to avoid re-creating the same star/plus rule multiple times
        self.created_nonterminals = {}
        # You may want to keep a global counter to generate unique names
        self.fresh_id = 0

    def fresh_nonterminal(self, base: str) -> str:
        """
        Create a fresh nonterminal name based on `base` to avoid collisions.
        E.g. "<digits_star_1>", "<digits_star_2>", ...
        """
        self.fresh_id += 1
        # Ensure it has angle brackets <...> in the fuzzingbook style
        return f"<{base}_{self.fresh_id}>"

    def visit(self, node: Node) -> List[str]:
        return node.accept(self)

    def default_result(self) -> List[str]:
        return []

    def aggregate_results(self, agg: List[str], result: List[str]) -> List[str]:
        return agg + result

    # -------------------------------------------------------
    # Terminal
    # -------------------------------------------------------
    def visitTerminalNode(self, node: TerminalNode) -> List[str]:
        return [str(node.symbol)]

    # -------------------------------------------------------
    # NonTerminal
    # -------------------------------------------------------
    def visitNonTerminalNode(self, node: NonTerminalNode) -> List[str]:
        """
        Return ['<symbol>'] and ensure that <symbol> has expansions in self.grammar_.
        Exactly how you fill those expansions depends on your global grammar structure.
        """
        nt_name = self.clean_names.visit(node)  # e.g. "<digits>"
        return [nt_name]

    # -------------------------------------------------------
    # Concatenation
    # -------------------------------------------------------
    def visitConcatenation(self, node: Concatenation) -> List[str]:
        # Collect expansions for each child, then do cartesian product
        lists_of_expansions = []
        for child in node.children():
            lists_of_expansions.append(self.visit(child))

        # Now cartesian product to form final expansions
        if not lists_of_expansions:
            return []

        result = lists_of_expansions[0]
        for expansions in lists_of_expansions[1:]:
            new_result = []
            for a in result:
                for b in expansions:
                    new_result.append(a + b)
            result = new_result

        return result

    # -------------------------------------------------------
    # Alternative
    # -------------------------------------------------------
    def visitAlternative(self, node: Alternative) -> List[str]:
        expansions = []
        for alternative in node.alternatives:
            expansions.extend(self.visit(alternative))
        return expansions

    # -------------------------------------------------------
    # Option (child?)
    # -------------------------------------------------------
    def visitOption(self, node: Option) -> List[str]:
        child_exps = self.visit(node.node)
        # either empty or the child's expansions
        return [""] + child_exps

    # -------------------------------------------------------
    # Star (child*)
    # -------------------------------------------------------
    def visitStar(self, node: Star) -> List[str]:
        """
        Transform child* into a new nonterminal <child_star> with expansions:
          <child_star> ::= "" | <child><child_star>
        Then return ["<child_star>"] to represent that place in the parent rule.
        """
        # 1) First, visit the child to see how it expands
        child_expansions = self.visit(node.node)

        # 2) We need a new nonterminal name for the star rule, e.g. <digits_star_1>
        #    Optionally, we can generate a stable key so the same node reuses the same rule
        child_key = ("STAR", repr(node.node))
        if child_key in self.created_nonterminals:
            # Already created a rule for child*
            star_nonterminal = self.created_nonterminals[child_key]
        else:
            star_nonterminal = self.fresh_nonterminal("star")
            self.created_nonterminals[child_key] = star_nonterminal

            # 3) We also define the expansions for star_nonterminal:
            #    We want: <star_nonterminal> ::= "" | <child><star_nonterminal>
            #    But <child> might be more than one expansion, so we must transform <child> into a new NT
            #    e.g. <child_wrapper>, because in fuzzingbook grammar each alternative is a string expansion.
            child_nt = self._wrap_in_nonterminal(child_expansions, "star_child")

            # expansions for the star NT
            # "" or <child_wrapper><star_nonterminal>
            expansions_for_star = [
                "",
                child_nt + star_nonterminal  # concatenation
            ]
            self.grammar_[star_nonterminal] = expansions_for_star

        return [star_nonterminal]

    # -------------------------------------------------------
    # Plus (child+)
    # -------------------------------------------------------
    def visitPlus(self, node: Plus) -> List[str]:
        """
        Transform child+ into a new nonterminal <child_plus> with expansions:
          <child_plus> ::= <child> | <child><child_plus>
        Then return ["<child_plus>"] to represent that place in the parent rule.
        """
        child_expansions = self.visit(node.node)

        child_key = ("PLUS", repr(node.node))
        if child_key in self.created_nonterminals:
            plus_nonterminal = self.created_nonterminals[child_key]
        else:
            plus_nonterminal = self.fresh_nonterminal("plus")
            self.created_nonterminals[child_key] = plus_nonterminal

            # Wrap child expansions in a new nonterminal
            child_nt = self._wrap_in_nonterminal(child_expansions, "plus_child")

            # expansions for the plus NT
            # <child_wrapper> or <child_wrapper><child_plus>
            expansions_for_plus = [
                child_nt,
                child_nt + plus_nonterminal
            ]
            self.grammar_[plus_nonterminal] = expansions_for_plus

        return [plus_nonterminal]

    # -------------------------------------------------------
    # Repetition (child{min,max})
    # -------------------------------------------------------
    def visitRepetition(self, node: Repetition) -> List[str]:
        """
        For child{min,max}, you can do a few approaches:
        1) Turn it into star/plus if min==0 or min==1, etc.
        2) Generate a new nonterminal with expansions for the range.
           e.g. <child_2_5> ::= <child><child> |
                                <child><child><child> |
                                <child><child><child><child> |
                                <child><child><child><child><child>
        """
        # If min=0 and max=1 => Option
        if node.min == 0 and node.max == 1:
            return self.visitOption(node)

        # If min=0 => treat as star with a restricted max, etc.
        # If min=1 => treat as plus with a restricted max.
        # Or define a brand-new nonterminal enumerating expansions up to max.
        child_expansions = self.visit(node.node)
        key = ("REPETITION", node.min, node.max, repr(node.node))
        if key in self.created_nonterminals:
            rep_nonterminal = self.created_nonterminals[key]
        else:
            rep_nonterminal = self.fresh_nonterminal(f"rep_{node.min}_{node.max}")
            self.created_nonterminals[key] = rep_nonterminal

            child_nt = self._wrap_in_nonterminal(child_expansions, "rep_child")

            # Build expansions for min..max times
            expansions = []
            for count in range(node.min, node.max + 1):
                if count == 0:
                    expansions.append("")
                else:
                    expansions.append(child_nt * count)
            self.grammar_[rep_nonterminal] = expansions

        return [rep_nonterminal]

    # -------------------------------------------------------
    # CharSet
    # -------------------------------------------------------
    def visitCharSet(self, node: CharSet) -> List[str]:
        """
        Return expansions that are each single character in the set.
        If you want a new nonterminal, you could also do so, but
        often it's fine to return them inline.
        """
        return list(node.chars)

    # -------------------------------------------------------
    # Helper: wrap expansions in a new nonterminal
    # -------------------------------------------------------
    def _wrap_in_nonterminal(self, expansions: List[str], base: str) -> str:
        """
        If you have multiple expansions for `child`, you can't directly
        do something like <child><star_nonterminal> in a single string
        unless <child> is itself a single expansion. It's better to define
        a new NT that references all possible expansions from `child`.

        e.g. if expansions = ["a", "b|c", ...] we store them as separate
        alternatives:
            <child_wrapper> ::= a | b|c | ...
        Then we return "<child_wrapper>" to use in other expansions.
        """
        wrapper_nt = self.fresh_nonterminal(base)
        # Each string in `expansions` is one alternative
        # NOTE: If expansions might contain '|', you should handle that carefully.
        self.grammar_[wrapper_nt] = list(set(expansions))  # store unique expansions
        return wrapper_nt
