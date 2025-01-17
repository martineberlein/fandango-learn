from typing import List, Iterable, Optional, Set, Tuple, Any
from abc import ABC, abstractmethod

from debugging_framework.input.oracle import OracleResult
from fandango.language.grammar import Grammar
from fandango.constraints.base import (
    Constraint,
)

from .learning.candidate import ConstraintCandidate, FandangoConstraintCandidate
from .data.input import Input as TestInput, FandangoInput
from .learning.metric import FitnessStrategy, RecallPriorityFitness
from .resources.patterns import Pattern
from .logger import LOGGER


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
        patterns: Optional[Iterable[str] | Iterable[Any]] = None,
    ):
        """
        Initialize the pattern candidate learner with a grammar and a pattern file or patterns.
        :param patterns: The patterns to use.
        """
        super().__init__()
        self.patterns = self.parse_patterns(patterns)

    @abstractmethod
    def parse_patterns(self, patterns):
        """
        Parse the patterns into constraints.
        """
        return set(patterns) if patterns else {}


class BaseFandangoLearner(PatternCandidateLearner, ABC):

    def __init__(
        self,
        grammar: Grammar,
        patterns: Optional[Iterable[str] | Iterable[Constraint]] = None,
        min_precision: float = 0.6,
        min_recall: float = 0.9,
        sorting_strategy: FitnessStrategy = RecallPriorityFitness(),
    ):
        super().__init__(patterns)
        self.grammar = grammar
        self.min_precision = min_precision
        self.min_recall = min_recall
        self.sorting_strategy = sorting_strategy

        self.candidates: Set[FandangoConstraintCandidate] = set()

    def parse_patterns(self, patterns):
        """
        Parse the patterns into constraints.
        """
        if not patterns:
            instantiated_patterns = {
                pat.instantiated_pattern for pat in Pattern.registry
            }
        else:
            assert all(isinstance(pat, Pattern) for pat in patterns)
            instantiated_patterns = {pat.instantiated_pattern for pat in patterns}
        LOGGER.info("Instantiated patterns: %s", len(instantiated_patterns))
        return instantiated_patterns

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

    @abstractmethod
    def learn_constraints(
        self, test_inputs: Set[FandangoInput], **kwargs
    ) -> Optional[List[FandangoConstraintCandidate]]:
        """
        Learn the candidates based on the test inputs.
        :param test_inputs:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

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
