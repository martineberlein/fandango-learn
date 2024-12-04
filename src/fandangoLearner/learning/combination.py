from typing import Tuple, Union, List
from abc import ABC, abstractmethod
import itertools

from fandango.constraints.base import ConjunctionConstraint, DisjunctionConstraint
from fandangoLearner.learning.candidate import FandangoConstraintCandidate


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
    """
    Disjunction processor that finds better disjunctions of the candidates.

    When constructing disjunctions in constraint learning, it is crucial to validate their effectiveness and relevance.
    Disjunctions inherently increase recall by relaxing constraints, but this often comes at the cost of reduced
    precision. To balance these trade-offs and tailor the validation process to specific application needs,
    multiple disjunction validation strategies are necessary.
    """

    def __init__(
        self, max_disjunction_size: int, min_precision: float, min_recall: float
    ):
        super().__init__(min_precision, min_recall)
        self.max_disjunction_size = max_disjunction_size

        self.validation_strategy: DisjunctionValidationStrategy = (
            DefaultDisjunctionValidation(self.min_precision)
        )

    def process(
        self, candidates: List[FandangoConstraintCandidate]
    ) -> List[FandangoConstraintCandidate]:
        """
        Iterates over all candidates to find the best disjunctions.
        :param candidates:
        :return: List of improved disjunction candidates
        """
        combinations = self.get_possible_disjunctions(candidates)

        disjunction_candidates = []
        for combination in combinations:
            if not self.check_minimum_recall(combination):
                continue

            disjunction: FandangoConstraintCandidate = combination[0]
            dis_list = [
                disjunction,
            ]
            valid = True
            for candidate in combination[1:]:
                disjunction = disjunction | candidate
                if not self.is_new_disjunction_valid(disjunction, dis_list):
                    valid = False
                dis_list.append(disjunction)

            if self.is_new_disjunction_valid(disjunction, combination) and valid:
                disjunction_candidates.append(disjunction)

        return disjunction_candidates

    def is_new_disjunction_valid(
        self,
        disjunction: FandangoConstraintCandidate,
        combination: Union[
            List[FandangoConstraintCandidate], Tuple[FandangoConstraintCandidate, ...]
        ],
    ) -> bool:
        """
        Check if the new disjunction is valid based on the minimum precision and the recall of the candidates in
        the combination. The precision of the new disjunction should be greater than the minimum precision and
        greater than the precision of the individual formula.
        """
        return self.validation_strategy.is_valid(disjunction, combination)

    def get_possible_disjunctions(
        self, candidate_set: List[FandangoConstraintCandidate]
    ) -> List[Tuple[FandangoConstraintCandidate, ...]]:
        """
        Get all possible disjunctions of the candidate set with a maximum size of max_disjunction_size.
        """
        combinations = []
        candidate_set_without_disjunctions = [
            candidate
            for candidate in candidate_set
            if not isinstance(candidate.constraint, DisjunctionConstraint)
        ]
        for level in range(2, self.max_disjunction_size + 1):
            for comb in itertools.combinations(
                candidate_set_without_disjunctions, level
            ):
                combinations.append(comb)
        return combinations


class DisjunctionValidationStrategy(ABC):
    """
    Abstract base class for disjunction validation strategies.
    """

    @abstractmethod
    def is_valid(
        self,
        disjunction: FandangoConstraintCandidate,
        combination: Union[
            List[FandangoConstraintCandidate], Tuple[FandangoConstraintCandidate, ...]
        ],
        **kwargs,
    ) -> bool:
        """
        Check if the disjunction is valid based on the implemented strategy.
        """
        pass


class DefaultDisjunctionValidation(DisjunctionValidationStrategy):
    """
    Default validation strategy for disjunctions.
    Ensures that the new disjunction's precision is greater than the minimum precision
    and also greater than the precision of each candidate in the combination.
    """

    def __init__(self, min_precision: float):
        self.min_precision = min_precision

    def is_valid(
        self,
        disjunction: FandangoConstraintCandidate,
        combination: Union[
            List[FandangoConstraintCandidate], Tuple[FandangoConstraintCandidate, ...]
        ],
        **kwargs,
    ) -> bool:
        new_precision = disjunction.precision()
        return new_precision > self.min_precision and all(
            new_precision > candidate.precision() for candidate in combination
        )


class PrecisionThresholdValidation(DisjunctionValidationStrategy):
    """
    Validates that the new disjunction's precision exceeds a minimum threshold.
    """

    def __init__(self, min_precision: float):
        self.min_precision = min_precision

    def is_valid(
        self,
        disjunction: FandangoConstraintCandidate,
        combination: Union[
            List[FandangoConstraintCandidate], Tuple[FandangoConstraintCandidate, ...]
        ],
        **kwargs,
    ) -> bool:
        return disjunction.precision() > self.min_precision


class RecallImprovementValidation(DisjunctionValidationStrategy):
    """
    Validates that the recall improvement outweighs precision loss by a specified factor.
    """

    def __init__(self, trade_off_factor: float = 2.0):
        self.trade_off_factor = trade_off_factor

    def is_valid(
        self,
        disjunction: FandangoConstraintCandidate,
        combination: Union[
            List[FandangoConstraintCandidate], Tuple[FandangoConstraintCandidate, ...]
        ],
        **kwargs,
    ) -> bool:
        new_precision = disjunction.precision()
        new_recall = disjunction.recall()

        precision_loss = max(
            candidate.precision() - new_precision for candidate in combination
        )
        recall_gain = max(new_recall - candidate.recall() for candidate in combination)
        return recall_gain >= precision_loss * self.trade_off_factor


class SpecificityValidation(DisjunctionValidationStrategy):
    """
    Validates that the new disjunction is not overly permissive by checking specificity.
    """

    def __init__(self, min_specificity: float = 0.1):
        self.min_specificity = min_specificity

    def is_valid(
        self,
        disjunction: FandangoConstraintCandidate,
        combination: Union[
            List[FandangoConstraintCandidate], Tuple[FandangoConstraintCandidate, ...]
        ],
        **kwargs,
    ) -> bool:
        return disjunction.specificity() >= self.min_specificity


class AveragePrecisionValidation(DisjunctionValidationStrategy):
    """
    Validates that the new disjunction's precision is not significantly below the average precision of the combination.
    """

    def __init__(self, precision_drop_threshold: float = 0.8):
        self.precision_drop_threshold = precision_drop_threshold

    def is_valid(
        self,
        disjunction: FandangoConstraintCandidate,
        combination: Union[
            List[FandangoConstraintCandidate], Tuple[FandangoConstraintCandidate, ...]
        ],
        **kwargs,
    ) -> bool:
        avg_precision = sum(candidate.precision() for candidate in combination) / len(
            combination
        )
        return disjunction.precision() >= avg_precision * self.precision_drop_threshold
