from typing import Iterable, List, Optional, Set, Tuple, Callable
from abc import ABC, abstractmethod
import copy

from debugging_framework.input.oracle import OracleResult
from fandango.language.grammar import Grammar

from .candidate import ConstraintCandidate, FandangoConstraintCandidate
from .input import Input as TestInput, FandangoInput
from .metric import FitnessStrategy, RecallPriorityLengthFitness


class ConstraintCandidateLearner(ABC):
    """
    A candidate learner is responsible for learning candidate formulas from a set
    """

    def __init__(self):
        self.candidates: List[ConstraintCandidate] = []

    @abstractmethod
    def learn_constraints(
        self, test_inputs: Iterable[TestInput], **kwargs
    ) -> Optional[List[ConstraintCandidate]]:
        """
        Learn the candidates based on the test inputs.
        :param test_inputs: The test inputs to learn the candidates from.
        :return Optional[List[Candidate]]: The learned candidates.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_candidates(self) -> Optional[List[ConstraintCandidate]]:
        """
        Get all constraints that have been learned.
        :return Optional[List[Candidate]]: The learned candidates.
        """
        return self.candidates

    @abstractmethod
    def get_best_candidates(self) -> Optional[List[ConstraintCandidate]]:
        """
        Get the best constraints that have been learned.
        :return Optional[List[Candidate]]: The best learned candidates.
        """
        raise NotImplementedError()


class PatternCandidateLearner(ConstraintCandidateLearner, ABC):
    """
    A candidate learner that learns formulas based on patterns from a pattern repository
    """

    def __init__(
        self,
        patterns: Optional[Iterable[str]] = None,
    ):
        """
        Initialize the pattern candidate learner with a grammar and a pattern file or patterns.
        :param patterns: The patterns to use.
        """
        super().__init__()
        self.patterns: Set[str] = set(patterns) if patterns else {}


class BaseFandangoLearner(PatternCandidateLearner):

    def __init__(
        self,
        grammar: Grammar,
        patterns: Optional[Iterable[str]] = None,
        min_precision: float = 0.6,
        min_recall: float = 0.9,
        sorting_strategy: FitnessStrategy = RecallPriorityLengthFitness(),
    ):
        super().__init__(patterns)
        self.grammar = grammar
        self.min_precision = min_precision
        self.min_recall = min_recall
        self.sorting_strategy = sorting_strategy

        self.candidates: List[FandangoConstraintCandidate] = []

    def meets_minimum_criteria(self, precision_value_, recall_value_):
        """
        Checks if the precision and recall values meet the minimum criteria.
        :param precision_value_: The precision value.
        :param recall_value_: The recall value.
        """
        return (
            precision_value_ >= self.min_precision and recall_value_ >= self.min_recall
        )

    def get_candidates(self) -> Optional[List[FandangoConstraintCandidate]]:
        """
        Returns the all the best formulas (ordered) based on the minimum precision and recall values.
        :return Optional[List[Candidate]]: The learned candidates.
        """

        return sorted(
            self.candidates,
            key=lambda c: self.sorting_strategy.evaluate(c),
            reverse=True,
        )

    def get_best_candidates(
        self,
    ) -> Optional[List[FandangoConstraintCandidate]]:
        """
        Returns the best formulas (ordered) based on the precision and recall values.
        Thus returns the best of the best formulas.
        :return Optional[List[Candidate]]: The best learned candidates.
        """
        candidates = self.get_candidates()
        if candidates:
            return self._get_best_candidates(candidates)

    def _get_best_candidates(
        self, candidates: List[FandangoConstraintCandidate]
    ) -> List[FandangoConstraintCandidate]:
        """
        Selects the best formulas based on the precision and recall values.
        :param candidates: The candidates to select the best from.
        :return List[Candidate]: The best learned candidates.
        """
        return [
            candidate
            for candidate in candidates
            if self.sorting_strategy.is_equal(candidate, candidates[0])
        ]

    def reset(self):
        """
        Resets the precision and recall truth tables. This is useful when the learner is used for multiple runs.
        Minimum precision and recall values are not reset.
        """
        self.candidates = []

    def learn_constraints(
        self, test_inputs: Set[FandangoInput], **kwargs
    ) -> Optional[List[FandangoConstraintCandidate]]:

        positive_inputs, negative_inputs = self.categorize_inputs(test_inputs)
        assert all(inp.oracle == OracleResult.FAILING for inp in positive_inputs)
        assert all(inp.oracle == OracleResult.PASSING for inp in negative_inputs)

        exclude_nonterminals: set[str] = set()
        atomic_candidates = self.compute_atomic_candidates(
            self.patterns, positive_inputs
        )

        # Todo: Implement learning of atomic and composite candidates
        # 1. sort test inputs according to usefulness; maybe k-paths? for atomic candidate construction we only need
        # a hand full
        # 2. learn atomic candidates from test inputs
        # 3. evaluate atomic candidates on all test inputs
        # 4. learn composite candidates from atomic candidates (disjunctions, conjunctions) - for conjunctions,
        # we need to check if the recall of the combination is greater than the minimum - for disjunctions,
        # we need to check if the specificity of the new disjunction is greater than the minimum
        # 5. evaluate composite candidates on all test inputs

        return None

    @staticmethod
    def categorize_inputs(
        test_inputs: Set[FandangoInput],
    ) -> Tuple[Set[FandangoInput], Set[FandangoInput]]:
        """
        Categorize the inputs into positive and negative inputs based on their oracle results.
        """
        positive_inputs = {
            inp for inp in test_inputs if inp.oracle == OracleResult.FAILING
        }
        negative_inputs = {
            inp for inp in test_inputs if inp.oracle == OracleResult.PASSING
        }
        return positive_inputs, negative_inputs

    def compute_atomic_candidates(self, patterns, positive_inputs):
        results = set()

        for pattern in patterns:
            instantiated_patterns = self.instantiate_pattern(pattern, positive_inputs)
            for instantiated_pattern in instantiated_patterns:
                results.add(instantiated_pattern)

    def instantiate_pattern(self, pattern, positive_inputs, exclude_non_terminals):
        steps: list[Callable] = [
            self._instantiate_non_terminal_placeholders,
            self._instantiate_int_placeholders,
        ]

        instantiated_patterns = set()
        for step in steps:
            instantiated_patterns = step(
                pattern, positive_inputs, exclude_non_terminals
            )

        assert True  # Check if all placeholders are resolved
        return set()

    def _instantiate_non_terminal_placeholders(
        self, pattern, positive_inputs, exclude_nonterminals
    ):
        pass

    def _instantiate_int_placeholders(
        self, pattern, positive_inputs, exclude_nonterminals
    ):
        pass
