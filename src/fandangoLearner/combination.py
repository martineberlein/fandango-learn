from typing import Tuple, Union, List
from abc import ABC, abstractmethod
import itertools

from fandango.constraints.base import ConjunctionConstraint

from .candidate import FandangoConstraintCandidate


class CombinationProcessor(ABC):

    def __init__(self, min_precision: float, min_recall: float):
        self.min_precision = min_precision
        self.min_recall = min_recall

    @abstractmethod
    def process(self, *args, **kwargs):
        raise NotImplementedError()

    def check_minimum_recall(
        self, candidates: Tuple[FandangoConstraintCandidate, ...]
    ) -> bool:
        """
        Check if the recall of the candidates in the combination is greater than the minimum
        """
        return all(candidate.recall() >= self.min_recall for candidate in candidates)


class ConjunctionProcessor(CombinationProcessor):
    """
    Conjunction processor that finds better conjunctions of the candidates.
    """

    def __init__(
        self, max_conjunction_size: int, min_precision: float, min_recall: float
    ):
        super().__init__(min_precision, min_recall)
        self.max_conjunction_size = max_conjunction_size

    def process(
        self, candidates: List[FandangoConstraintCandidate]
    ) -> List[FandangoConstraintCandidate]:
        """
        Iterates of all candidates to find the best conjunctions.
        :param candidates:
        :return:
        """
        combinations = self.get_possible_conjunctions(candidates)

        conjunction_candidates = []
        for combination in combinations:
            # check min recall
            if not self.check_minimum_recall(combination):
                continue
            conjunction: FandangoConstraintCandidate = combination[0]
            con_list = [
                conjunction,
            ]
            valid = True
            for candidate in combination[1:]:
                conjunction = conjunction & candidate
                if not self.is_new_conjunction_valid(conjunction, con_list):
                    valid = False
                con_list.append(conjunction)
            if self.is_new_conjunction_valid(conjunction, combination) and valid:
                conjunction_candidates.append(conjunction)

        return conjunction_candidates

    def is_new_conjunction_valid(
        self,
        conjunction: FandangoConstraintCandidate,
        combination: Union[
            List[FandangoConstraintCandidate], Tuple[FandangoConstraintCandidate, ...]
        ],
    ) -> bool:
        """
        Check if the new conjunction is valid based on the minimum specificity and the recall of the candidates in
        the combination. The specificity of the new conjunction should be greater than the minimum specificity and
        the specificity of the conjunction should be greater than the specificity of the individual formula.
        """
        new_precision = conjunction.precision()
        return new_precision > self.min_precision and all(
            new_precision > candidate.precision() for candidate in combination
        )

    def get_possible_conjunctions(
        self, candidate_set: List[FandangoConstraintCandidate]
    ) -> List[Tuple[FandangoConstraintCandidate, ...]]:
        """
        Get all possible conjunctions of the candidate set with a maximum size of max_conjunction_size.
        """
        combinations = []
        candidate_set_without_conjunctions = [
            candidate
            for candidate in candidate_set
            if not isinstance(candidate.constraint, ConjunctionConstraint)
        ]
        for level in range(2, self.max_conjunction_size + 1):
            for comb in itertools.combinations(
                candidate_set_without_conjunctions, level
            ):
                combinations.append(comb)
        return combinations


class DisjunctionProcessor(CombinationProcessor):
    pass
