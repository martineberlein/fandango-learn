from typing import Set, Optional, List

from fandango.language.symbol import NonTerminal

from fdlearn.types import OracleType
from fdlearn.data import FandangoInput
from fdlearn.learner import FandangoLearner
from fdlearn.learning.value_map import ValueMap, ReachabilityMap


class Rule:

    def __init__(self, predicates: set=None):
        self.predicates = predicates if predicates else set()

    def __contains__(self, item):
        return item in self.predicates

    def add(self, item):
        self.predicates.add(item)

    def __str__(self):
        return "(" + " and ".join(
            str(constraint.constraint) for constraint in self.predicates
        ) + ")"


class RuleSet:

    def __init__(self, rules: list[Rule]=None):
        self.rules: list[Rule] = rules if rules else []

    def add(self, rule):
        self.rules.append(rule)

    def __str__(self):
        return " or ".join(
            str(rule) for rule in self.rules
        )

class RuleInductionLearner(FandangoLearner):


    def instantiate_patterns(self, test_inputs: set[FandangoInput], relevant_non_terminals: Set[NonTerminal] = None,):

        relevant_non_terminals = self.get_relevant_non_terminals(
            relevant_non_terminals, test_inputs
        )

        positive_inputs, negative_inputs = self.categorize_inputs(test_inputs)
        self.update_inputs(positive_inputs, negative_inputs)

        sorted_positive_inputs = self.sort_and_filter_positive_inputs(
            self.all_positive_inputs
        )

        value_map = ValueMap.from_inputs(relevant_non_terminals, sorted_positive_inputs)
        reachability_map = ReachabilityMap(self.grammar)

        instantiated_candidates = self.pattern_processor.instantiate_patterns(
            relevant_non_terminals, sorted_positive_inputs, value_maps=value_map, reachability_map=reachability_map
        )

        return instantiated_candidates

    def learn_constraints(
        self,
        test_inputs: set[FandangoInput] | set[str],
        relevant_non_terminals: Set[NonTerminal] = None,
        oracle: OracleType = None,
        **kwargs,
    ) -> RuleSet:
        if any(isinstance(inp, str) for inp in test_inputs):
            test_inputs = self.parse_string_initial_inputs(test_inputs, oracle)

        patterns = self.instantiate_patterns(test_inputs, relevant_non_terminals)

        rule_set = RuleSet()
        positives = self.all_positive_inputs

        while positives:
            # start with empty rule
            rule = Rule()
            covered = [d for d in test_inputs if d in positives or not d.oracle.is_failing()]
            improved = True

            while improved:
                improved = False
                P = sum(inp.oracle.is_failing() for inp in covered)
                N = sum(not inp.oracle.is_failing() for inp in covered)

                best_gain = -float("inf")
                best_pred = None
                best_new_cover = None

                for pattern in patterns:
                    if pattern in rule:
                        continue  # already in rule

                    new_cover = [inp for inp in covered if pattern.check(inp)]
                    P_new = sum(inp.oracle.is_failing() for inp in new_cover)
                    N_new = sum(not inp.oracle.is_failing() for inp in new_cover)

                    gain = foil_gain(P, N, P_new, N_new)
                    if gain > best_gain:
                        best_gain = gain
                        best_pred = pattern
                        best_new_cover = new_cover

                if best_pred and best_gain > 0:
                    rule.add(best_pred)
                    covered = best_new_cover
                    improved = True
            # finalize rule
            rule_set.add(rule)

            # remove covered positives
            covered_pos = {d for d in covered if d.oracle.is_failing()}
            positives = {p for p in positives if p not in covered_pos}

        return rule_set





import math

def foil_gain(P, N, P_new, N_new):
    """FOIL-Gain for adding a predicate"""
    if P_new == 0:  # rule covers no positives
        return -float("inf")
    return P_new * (math.log2(P_new / (P_new + N_new)) -
                    math.log2(P / (P + N)))

def induce_rules(X, y, predicates):
    """
    X: list of inputs
    y: list of binary labels (0 or 1)
    predicates: list of (name, function) where function(x) -> bool
    """
    data = list(zip(X, y))
    rules = []

    # remaining positives
    positives = [d for d in data if d[1] == 1]

    while positives:
        # start with empty rule
        rule_preds = []
        covered = data[:]   # all examples initially
        improved = True

        while improved:
            improved = False
            P = sum(lbl == 1 for (_, lbl) in covered)
            N = sum(lbl == 0 for (_, lbl) in covered)

            best_gain = -float("inf")
            best_pred = None
            best_new_cover = None

            for name, pred in predicates:
                if name in rule_preds:
                    continue  # already in rule

                new_cover = [(x,lbl) for (x,lbl) in covered if pred(x)]
                P_new = sum(lbl == 1 for (_, lbl) in new_cover)
                N_new = sum(lbl == 0 for (_, lbl) in new_cover)

                gain = foil_gain(P, N, P_new, N_new)
                if gain > best_gain:
                    best_gain = gain
                    best_pred = name
                    best_new_cover = new_cover

            if best_pred and best_gain > 0:
                rule_preds.append(best_pred)
                covered = best_new_cover
                improved = True

        # finalize rule
        rules.append(rule_preds)

        # remove covered positives
        covered_pos = [d for d in covered if d[1] == 1]
        positives = [p for p in positives if p not in covered_pos]

    return rules