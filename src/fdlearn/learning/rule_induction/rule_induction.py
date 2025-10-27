import math
import time
from typing import Iterable, Optional
from tqdm import tqdm

from fandango.language.grammar import Grammar
from fandango.constraints.base import Constraint, DisjunctionConstraint, ConjunctionConstraint
from fandango.language.symbol import NonTerminal

from fdlearn.logger import LOGGER, LoggerLevel
from fdlearn.resources.patterns import Pattern
from fdlearn.learning.candidate import FandangoConstraintCandidate
from fdlearn.types import OracleType
from fdlearn.data import FandangoInput, OracleResult
from fdlearn.learner import FandangoLearner
from fdlearn.learning.value_map import ValueMap, ReachabilityMap


def foil_gain(P, N, P_new, N_new):
    """FOIL-Gain for adding a predicate"""
    if P_new == 0:  # rule covers no positives
        return -float("inf")
    return P_new * (math.log2(P_new / (P_new + N_new)) - math.log2(P / (P + N)))


class Rule:

    def __init__(self, predicates: set = None):
        self.predicates: set[FandangoConstraintCandidate] = predicates if predicates else set()

    def __contains__(self, item):
        return item in self.predicates

    def __len__(self) -> int:
        return len(self.predicates)

    def add(self, item):
        self.predicates.add(item)

    def to_constraint(self) -> ConjunctionConstraint:
        constraints = [predicate.constraint for predicate in self.predicates]
        return ConjunctionConstraint(
            constraints=constraints
        )

    def to_constraint_candidate(self) -> FandangoConstraintCandidate:
        return FandangoConstraintCandidate(self.to_constraint())

    def __str__(self):
        return (
            "("
            + " AND ".join(str(constraint.constraint) for constraint in self.predicates)
            + ")"
        )


class RuleSet:

    def __init__(self, rules: list[Rule] = None):
        self.rules: list[Rule] = rules if rules else []

    def add(self, rule):
        self.rules.append(rule)

    def to_constraint(self) -> DisjunctionConstraint:
        constraints = [rule.to_constraint() for rule in self.rules]
        return DisjunctionConstraint(
            constraints=constraints
        )

    def to_constraint_candidate(self) -> FandangoConstraintCandidate:
        return FandangoConstraintCandidate(
            self.to_constraint()
        )

    def __str__(self):
        return " OR ".join(str(rule) for rule in self.rules)


class RuleInductionLearner(FandangoLearner):
    """Learns rules using a FOIL-like induction algorithm."""

    def __init__(
        self,
        grammar: Grammar,
        patterns: Optional[Iterable[str | Pattern]] = None,
        logger_level: Optional[LoggerLevel] = None,
        **kwargs,
    ):
        """
        Initializes the FandangoLearner with a grammar and optional patterns.

        Args:
            grammar (Grammar): The grammar used for parsing and learning constraints.
            patterns (Optional[Iterable[str]]): A collection of patterns to be used in the learning process.
            **kwargs: Additional arguments for customization.
        """

        if logger_level is not None:
            LOGGER.setLevel(logger_level.value)

        super().__init__(grammar, patterns, **kwargs)

        self.positive_learning_size = 10

    def instantiate_patterns(
        self,
        test_inputs: set[FandangoInput],
        relevant_non_terminals: Optional[set[NonTerminal]] = None,
    ):
        """
        Instantiates the pattern predicates.

        :param test_inputs:
        :param relevant_non_terminals:
        :return: ConstraintCandidates
        """
        relevant_non_terminals = self.get_relevant_non_terminals(
            relevant_non_terminals, test_inputs
        )

        pos_inputs, neg_inputs = self.categorize_inputs(test_inputs)
        self.update_inputs(pos_inputs, neg_inputs)

        sorted_pos_inputs = self.sort_and_filter_positive_inputs(
            self.all_positive_inputs
        )

        value_map = ValueMap.from_inputs(relevant_non_terminals, sorted_pos_inputs)
        reach_map = ReachabilityMap(self.grammar)

        return self.pattern_processor.instantiate_patterns(
            relevant_non_terminals,
            sorted_pos_inputs,
            value_maps=value_map,
            reachability_map=reach_map,
            use_filtered_integer_values=True,
        )

    def learn_constraints(
        self,
        test_inputs: set[FandangoInput] | set[str],
        relevant_non_terminals: Optional[set[NonTerminal]] = None,
        oracle: Optional[OracleType] = None,
        **kwargs,
    ) -> list[FandangoConstraintCandidate]:
        if any(isinstance(inp, str) for inp in test_inputs):
            test_inputs = self.parse_string_initial_inputs(test_inputs, oracle)

        patterns = self.instantiate_patterns(test_inputs, relevant_non_terminals)
        LOGGER.info(f"Instantiated {len(patterns)} candidates from pattern. ")
        positives = set(self.all_positive_inputs)

        rule_set = RuleSet()

        while positives:
            rule, covered = self._learn_single_rule(patterns, test_inputs, positives)
            rule_set.add(rule)
            positives -= {d for d in covered if d.oracle.is_failing()}

        return [rule_set.to_constraint_candidate()]

    def _learn_single_rule(
        self,
        patterns: Iterable,
        test_inputs: set[FandangoInput],
        positives: set[FandangoInput],
    ) -> tuple[Rule, list[FandangoInput]]:
        """Constructs one rule that covers part of the positives."""
        rule = Rule()
        covered = self._cover_inputs(test_inputs, positives)
        improved = True

        while improved:
            improved = False
            P, N = self._count_pos_neg(covered)
            best_pred, best_cover, best_gain = self._select_best_predicate(
                patterns, rule, covered, P, N
            )

            if best_pred and best_gain > 0:
                rule.add(best_pred)
                covered = best_cover
                improved = True

        return rule, covered

    @staticmethod
    def _cover_inputs(test_inputs, positives):
        """Return inputs relevant to current rule."""
        return [d for d in test_inputs if d in positives or not d.oracle.is_failing()]

    @staticmethod
    def _count_pos_neg(inputs: list[FandangoInput]) -> tuple[int, int]:
        P = sum(inp.oracle.is_failing() for inp in inputs)
        N = len(inputs) - P
        return P, N

    def _select_best_predicate(self, patterns, rule, covered, P, N):
        best_gain = float("-inf")
        best_pred = best_cover = None
        positives_only = [i for i in covered if i.oracle.is_failing()]

        for pattern in tqdm(patterns, total=len(patterns)):
            if pattern in rule:
                continue

            pattern.evaluate(positives_only)
            # posi = [i for i in positives_only if pattern.check(i)]
            if pattern.recall() < self.min_recall:
                continue

            new_cover = [i for i in covered if pattern.check(i)]

            P_new, N_new = self._count_pos_neg(new_cover)
            gain = foil_gain(P, N, P_new, N_new)

            if gain > best_gain:
                best_gain, best_pred, best_cover = gain, pattern, new_cover

        return best_pred, best_cover, best_gain



class RuleInductionLearnerBeamSearch(FandangoLearner):
    """Learns rules using a multi-objective beam search over pattern predicates."""

    def __init__(
        self,
        grammar: Grammar,
        patterns: Optional[Iterable[str | Pattern]] = None,
        logger_level: Optional[LoggerLevel] = None,
        **kwargs,
    ):
        if logger_level is not None:
            LOGGER.setLevel(logger_level.value)
        super().__init__(grammar, patterns, **kwargs)

    # --------------------------------------------------------------------------
    # Pattern instantiation
    # --------------------------------------------------------------------------
    def instantiate_patterns(
        self,
        test_inputs: set[FandangoInput],
        relevant_non_terminals: Optional[set[NonTerminal]] = None,
    ):
        relevant_non_terminals = self.get_relevant_non_terminals(
            relevant_non_terminals, test_inputs
        )

        pos_inputs, neg_inputs = self.categorize_inputs(test_inputs)
        self.update_inputs(pos_inputs, neg_inputs)

        sorted_pos_inputs = self.sort_and_filter_positive_inputs(
            self.all_positive_inputs
        )

        value_map = ValueMap.from_inputs(relevant_non_terminals, sorted_pos_inputs)
        reach_map = ReachabilityMap(self.grammar)

        return self.pattern_processor.instantiate_patterns(
            relevant_non_terminals,
            sorted_pos_inputs,
            value_maps=value_map,
            reachability_map=reach_map,
            use_filtered_integer_values=False,
        )

    # --------------------------------------------------------------------------
    # Core learning loop
    # --------------------------------------------------------------------------
    def learn_constraints(
        self,
        test_inputs: set[FandangoInput] | set[str],
        relevant_non_terminals: Optional[set[NonTerminal]] = None,
        oracle: Optional[OracleType] = None,
        **kwargs,
    ) -> list[FandangoConstraintCandidate]:

        if any(isinstance(inp, str) for inp in test_inputs):
            test_inputs = self.parse_string_initial_inputs(test_inputs, oracle)

        patterns = self.instantiate_patterns(test_inputs, relevant_non_terminals)
        positives = set(self.all_positive_inputs)

        rule_set = RuleSet()

        while positives:
            rule, covered = self._learn_single_rule(patterns, test_inputs, positives)
            rule_set.add(rule)
            positives -= {d for d in covered if d.oracle.is_failing()}

        return [rule_set.to_constraint_candidate()]

    # --------------------------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------------------------
    @staticmethod
    def _cover_inputs(test_inputs, positives):
        return [d for d in test_inputs if d in positives or not d.oracle.is_failing()]

    @staticmethod
    def _count_pos_neg(inputs: list[FandangoInput]) -> tuple[int, int]:
        P = sum(inp.oracle.is_failing() for inp in inputs)
        N = len(inputs) - P
        return P, N

    # --------------------------------------------------------------------------
    # Multi-objective beam components
    # --------------------------------------------------------------------------
    def _precision_recall(self, covered):
        P, N = self._count_pos_neg(covered)
        TP = P
        FP = N
        total_pos = sum(i.oracle.is_failing() for i in self.all_positive_inputs)
        recall = TP / total_pos if total_pos else 0.0
        precision = TP / (TP + FP) if TP + FP else 0.0
        return precision, recall

    @staticmethod
    def _dominates(a, b):
        # a,b = (1-P, 1-R, length)
        return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))

    # --------------------------------------------------------------------------
    # Beam search replacing FOIL gain
    # --------------------------------------------------------------------------
    def _select_best_predicate(
        self,
        patterns: Iterable[FandangoConstraintCandidate],
        rule: Rule,
        covered: list[FandangoInput],
        P: int,
        N: int,
        beam_width: int = 20,
        max_len: int = 3,
        beta: float = 1.0,
    ):
        beam = [(rule, covered)]
        pareto = []

        for depth in range(1, max_len + 1):
            candidates = []
            for r, cov in beam:
                used = set(r.predicates)
                for pat in patterns:
                    if pat in used:
                        continue
                    new_cov = [i for i in cov if pat.check(i)]
                    if not new_cov:
                        continue
                    prec, rec = self._precision_recall(new_cov)
                    length = len(r.predicates) + 1
                    new_rule = Rule(set(r.predicates))  # copy current predicates
                    new_rule.add(pat)
                    candidates.append((new_rule, new_cov, 1 - prec, 1 - rec, length))

            if not candidates:
                break

            # Pareto filter
            non_dom = []
            for c in candidates:
                if any(self._dominates(o[2:], c[2:]) for o in candidates if o != c):
                    continue
                non_dom.append(c)

            pareto.extend(non_dom)

            # Beam tie-break by F_beta
            scored = []
            for r_, cov_, _, _, _ in non_dom:
                TP = sum(i.oracle.is_failing() for i in cov_)
                FP = len(cov_) - TP
                FN = sum(i.oracle.is_failing() for i in self.all_positive_inputs) - TP
                num = (1 + beta ** 2) * TP
                den = (1 + beta ** 2) * TP + beta ** 2 * FN + FP
                fbeta = num / den if den > 0 else 0.0
                # compute precision here again for tie-breaking
                prec, _ = self._precision_recall(cov_)
                scored.append((fbeta, prec, -len(r_.predicates), r_, cov_))

            # sort only by numeric keys
            scored.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
            beam = [(r_, cov_) for _, _, _, r_, cov_ in scored[:beam_width]]

        # pick final best predicate
        if not pareto:
            return None, None, 0.0
        best = max(pareto, key=lambda x: (1 - x[2], 1 - x[3]))  # best P,R
        best_rule, best_cover = best[0], best[1]
        gain = len(best_cover) / max(len(covered), 1)

        # Extract the predicate just added compared to the parent rule
        new_predicates = best_rule.predicates - rule.predicates
        best_pred = next(iter(new_predicates)) if new_predicates else None

        return best_pred, best_cover, gain

    # --------------------------------------------------------------------------
    # Single-rule construction loop
    # --------------------------------------------------------------------------
    def _learn_single_rule(
        self,
        patterns: Iterable[FandangoConstraintCandidate],
        test_inputs: set[FandangoInput],
        positives: set[FandangoInput],
    ) -> tuple[Rule, list[FandangoInput]]:

        rule = Rule()
        covered = self._cover_inputs(test_inputs, positives)
        improved = True

        max_iters = 50
        iters = 0
        while improved and iters < max_iters:
            print(iters, rule)
            iters += 1
            improved = False
            P, N = self._count_pos_neg(covered)
            best_pred, best_cover, best_gain = self._select_best_predicate(
                patterns, rule, covered, P, N
            )

            if best_pred and best_gain > 0:
                rule.add(best_pred)
                covered = best_cover
                improved = True

        return rule, covered