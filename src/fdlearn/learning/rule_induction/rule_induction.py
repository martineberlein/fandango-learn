import math
from dataclasses import dataclass, field
from typing import Iterable, Optional, Sequence

from tqdm import tqdm

from fandango.language.grammar import Grammar
from fandango.constraints.base import ConjunctionConstraint, DisjunctionConstraint
from fandango.language.symbol import NonTerminal

from fdlearn.logger import LOGGER, LoggerLevel
from fdlearn.resources.patterns import Pattern
from fdlearn.learning.candidate import FandangoConstraintCandidate
from fdlearn.types import OracleType
from fdlearn.data import FandangoInput
from fdlearn.learner import FandangoLearner
from fdlearn.learning.value_map import ValueMap, ReachabilityMap


EPS = 1e-12


# -------------------------
# Scoring / selection logic
# -------------------------

@dataclass(frozen=True)
class InductionConfig:
    """
    Configuration for rule induction.

    Attributes
    ----------
    target_covered_frac:
        Stop after this fraction of positives is covered by the RuleSet.
        Example: 0.8 means: cover 80% of positives.
    min_pos_coverage_frac_per_predicate:
        Minimum fraction of *current positives in the covered set* that a predicate must cover
        to be eligible for selection inside a rule.
        Example: 0.3 means: predicate must match at least 30% of current positives.
    length_lambda:
        Regularization strength for rule length. Larger -> shorter rules preferred.
    improvement_tol:
        Numerical tolerance for accepting a score improvement.
    """
    target_covered_frac: float = 0.8
    min_pos_coverage_frac_per_predicate: float = 0.30
    length_lambda: float = 0.01
    improvement_tol: float = 1e-12


def score_precision_len(P_new: int, N_new: int, rule_len_new: int, *, length_lambda: float) -> float:
    """
    Score a candidate rule after adding a predicate.

    Currently: precision - lambda * rule_length

    Returns
    -------
    float
        Higher is better.
    """
    precision = P_new / (P_new + N_new + EPS)
    return precision - length_lambda * rule_len_new


# -------------------------
# Rule representation
# -------------------------

@dataclass
class Rule:
    """A conjunction (AND) of predicate candidates."""
    predicates: set[FandangoConstraintCandidate] = field(default_factory=set)

    def __contains__(self, item: FandangoConstraintCandidate) -> bool:
        return item in self.predicates

    def __len__(self) -> int:
        return len(self.predicates)

    def add(self, item: FandangoConstraintCandidate) -> None:
        self.predicates.add(item)

    def to_constraint(self) -> ConjunctionConstraint:
        return ConjunctionConstraint(constraints=[p.constraint for p in self.predicates])

    def to_constraint_candidate(self) -> FandangoConstraintCandidate:
        return FandangoConstraintCandidate(self.to_constraint())

    def __str__(self) -> str:
        inner = " AND ".join(str(p.constraint) for p in self.predicates)
        return f"({inner})"


@dataclass
class RuleSet:
    """A disjunction (OR) of rules."""
    rules: list[Rule] = field(default_factory=list)

    def add(self, rule: Rule) -> None:
        self.rules.append(rule)

    def to_constraint(self) -> DisjunctionConstraint:
        return DisjunctionConstraint(constraints=[r.to_constraint() for r in self.rules])

    def to_constraint_candidate(self) -> FandangoConstraintCandidate:
        return FandangoConstraintCandidate(self.to_constraint())

    def __str__(self) -> str:
        return " OR ".join(str(r) for r in self.rules)


# -------------------------
# Learner
# -------------------------

class RuleInductionLearner(FandangoLearner):
    """
    Learns a RuleSet using a FOIL-like induction algorithm.

    Outer loop:
        - repeatedly learn a rule that covers some remaining positives
        - remove newly-covered positives
        - stop when `target_covered_frac` achieved or no progress possible

    Inner loop (rule learning):
        - start with an empty rule, and a 'covered' dataset consisting of:
            * all current positives
            * all negatives (for precision estimation)
        - greedily add the best predicate until no score improvement
    """

    def __init__(
        self,
        grammar: Grammar,
        patterns: Optional[Iterable[str | Pattern]] = None,
        logger_level: Optional[LoggerLevel] = None,
        config: Optional[InductionConfig] = None,
        **kwargs,
    ):
        if logger_level is not None:
            LOGGER.setLevel(logger_level.value)

        super().__init__(grammar, patterns, **kwargs)
        self.config = config or InductionConfig()

        # existing knob in your codebase; leaving it but not used here directly
        self.positive_learning_size = 100

    # ---- pattern instantiation ----

    def instantiate_patterns(
        self,
        test_inputs: set[FandangoInput],
        relevant_non_terminals: Optional[set[NonTerminal]] = None,
    ):
        """
        Instantiate pattern predicates from the current test inputs.

        Parameters
        ----------
        test_inputs:
            Parsed inputs with oracle results attached.
        relevant_non_terminals:
            Optional restriction for which grammar symbols to consider.

        Returns
        -------
        set
            A set of pattern-instantiated candidates usable as predicates.
        """
        relevant_non_terminals = self.get_relevant_non_terminals(
            relevant_non_terminals, test_inputs
        )

        pos_inputs, neg_inputs = self.categorize_inputs(test_inputs)
        self.update_inputs(pos_inputs, neg_inputs)

        sorted_pos_inputs = self.sort_and_filter_positive_inputs(self.all_positive_inputs)

        value_map = ValueMap.from_inputs(relevant_non_terminals, sorted_pos_inputs)
        reach_map = ReachabilityMap(self.grammar)

        return self.pattern_processor.instantiate_patterns(
            relevant_non_terminals,
            sorted_pos_inputs,
            value_maps=value_map,
            reachability_map=reach_map,
            use_filtered_integer_values=True,
        )

    # ---- main entrypoint ----

    def learn_constraints(
        self,
        test_inputs: set[FandangoInput] | set[str],
        relevant_non_terminals: Optional[set[NonTerminal]] = None,
        oracle: Optional[OracleType] = None,
        **kwargs,
    ) -> list[FandangoConstraintCandidate]:
        """
        Learn a constraint candidate representing a disjunction of induced rules.

        Returns
        -------
        list[FandangoConstraintCandidate]
            A singleton list containing the final RuleSet as one constraint candidate.
        """
        if any(isinstance(inp, str) for inp in test_inputs):
            test_inputs = self.parse_string_initial_inputs(test_inputs, oracle)

        patterns = self.instantiate_patterns(test_inputs, relevant_non_terminals)
        LOGGER.info(f"Instantiated {len(patterns)} candidates from pattern.")

        positives = set(self.all_positive_inputs)
        total_pos = len(positives)
        if total_pos == 0:
            return [RuleSet().to_constraint_candidate()]

        ruleset = RuleSet()
        covered_pos: set[FandangoInput] = set()

        while len(covered_pos) / total_pos < self.config.target_covered_frac:
            rule, covered_pool = self._learn_single_rule(patterns, test_inputs, positives)

            newly_covered = {
                d for d in covered_pool
                if d in positives and d.oracle.is_failing()
            }

            # No progress => stop.
            if not newly_covered:
                break

            ruleset.add(rule)
            covered_pos |= newly_covered
            positives -= newly_covered

            # Optional early stop when no positives remain.
            if not positives:
                break

        return [ruleset.to_constraint_candidate()]

    # ---- inner loop: learn one rule ----

    def _learn_single_rule(
        self,
        patterns: set,
        test_inputs: set[FandangoInput],
        positives: set[FandangoInput],
    ) -> tuple[Rule, list[FandangoInput]]:
        """
        Construct one rule that covers part of the remaining positives.

        Returns
        -------
        (Rule, list[FandangoInput])
            The learned rule and the final covered pool under that rule.
        """
        rule = Rule()
        covered_pool = self._build_covered_pool(test_inputs, positives)

        P, N = self._count_pos_neg(covered_pool)
        prev_score = score_precision_len(
            P_new=P, N_new=N, rule_len_new=len(rule),
            length_lambda=self.config.length_lambda,
        )

        while True:
            P, N = self._count_pos_neg(covered_pool)

            best_pred, best_cover, best_score = self._select_best_predicate(
                patterns=patterns,
                rule=rule,
                covered_pool=covered_pool,
                P=P,
                N=N,
            )

            if best_pred is None:
                break

            if best_score <= prev_score + self.config.improvement_tol:
                break

            rule.add(best_pred)
            covered_pool = best_cover
            prev_score = best_score

        return rule, covered_pool

    # ---- helpers ----

    @staticmethod
    def _build_covered_pool(
        test_inputs: set[FandangoInput],
        positives: set[FandangoInput],
    ) -> list[FandangoInput]:
        """
        Pool used to evaluate precision for the *current* rule.

        Includes:
        - all remaining positives (to ensure rule can cover them)
        - all negatives (to measure false positives)

        This matches your original semantics:
            positives OR not failing
        """
        return [d for d in test_inputs if (d in positives) or (not d.oracle.is_failing())]

    @staticmethod
    def _count_pos_neg(inputs: Sequence[FandangoInput]) -> tuple[int, int]:
        """Count failing (P) and non-failing (N) inputs in a list."""
        P = sum(inp.oracle.is_failing() for inp in inputs)
        N = len(inputs) - P
        return P, N

    def _select_best_predicate(
        self,
        patterns,
        rule: Rule,
        covered_pool: list[FandangoInput],
        P: int,
        N: int,
    ):
        """
        Select the best next predicate to add to the rule.

        Selection constraints
        ---------------------
        A predicate must cover at least `min_pos_coverage_frac_per_predicate` of the
        *current positives inside covered_pool*.

        Objective
        ---------
        Maximize: precision - lambda * rule_length
        """
        best_score = float("-inf")
        best_pred = None
        best_cover = None

        positives_only = [i for i in covered_pool if i.oracle.is_failing()]
        min_pos_cov = max(
            1,
            int(self.config.min_pos_coverage_frac_per_predicate * len(positives_only)),
        )

        debug_top: list[tuple[float, int, object]] = []

        for pattern in tqdm(patterns, total=len(patterns)):
            if pattern in rule:
                continue

            # If patterns maintain internal stats, keep this call.
            # If not needed for a pattern implementation, it should be a no-op.
            pattern.evaluate(positives_only)

            # Enforce minimum positive coverage constraint.
            p_cov = sum(1 for i in positives_only if pattern.check(i))
            if p_cov < min_pos_cov:
                continue

            new_cover = [i for i in covered_pool if pattern.check(i)]
            P_new, N_new = self._count_pos_neg(new_cover)

            score = score_precision_len(
                P_new=P_new,
                N_new=N_new,
                rule_len_new=len(rule) + 1,
                length_lambda=self.config.length_lambda,
            )

            debug_top.append((score, len(new_cover), pattern))

            if score > best_score:
                best_score = score
                best_pred = pattern
                best_cover = new_cover

        # Keep your debugging, but make it non-spammy.
        debug_top.sort(key=lambda x: x[0], reverse=True)
        for row in debug_top[:10]:
            LOGGER.debug(f"cand score={row[0]:.6f} cover={row[1]} pred={row[2]}")

        LOGGER.debug(f"selected score={best_score:.6f} pred={best_pred}")
        return best_pred, best_cover, best_score