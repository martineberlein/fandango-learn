from abc import ABC, abstractmethod
from typing import Tuple, Union, List, Set
import itertools

from fandango.constraints.base import ConjunctionConstraint, DisjunctionConstraint

from fdlearn.learning.candidate import FandangoConstraintCandidate, CandidateSet
from fdlearn.logger import LOGGER
from fdlearn.data.oracle import OracleResult


def build_conjunction(
    candidates: tuple[FandangoConstraintCandidate, ...],
) -> FandangoConstraintCandidate:
    assert len(candidates) >= 2, "Need at least two candidates for conjunction"

    first = candidates[0]
    cache_keys = first.cache.keys()

    for other in candidates[1:]:
        assert (
            other.cache.keys() == cache_keys
        ), "All candidates must share the same cache keys"

    new_cache = {}
    new_failing, new_passing = [], []

    for inp in cache_keys:
        conjunction_value = all(c.cache[inp] for c in candidates)
        new_cache[inp] = conjunction_value

        if inp.oracle == OracleResult.FAILING:
            new_failing.append(conjunction_value)
        else:
            new_passing.append(conjunction_value)

    new_constraint = ConjunctionConstraint(
        [c.constraint for c in candidates],
        local_variables=first.constraint.local_variables,
        global_variables=first.constraint.global_variables,
    )

    return FandangoConstraintCandidate(
        constraint=new_constraint,
        failing_inputs_eval_results=new_failing,
        passing_inputs_eval_results=new_passing,
        cache=new_cache,
    )


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

    def process(self, candidates: CandidateSet) -> Set[FandangoConstraintCandidate]:
        """
        Iterates of all candidates to find the best conjunctions.
        :param candidates:
        :return:
        """
        combinations = self.get_possible_conjunctions(candidates)

        conjunction_candidates = set()
        for combination in combinations:
            # check min recall
            # if not self.check_minimum_recall(combination):
            #     print("Lol")
            #     continue
            # conjunction: FandangoConstraintCandidate = combination[0]
            # # con_list = [
            # #     conjunction,
            # # ]
            # for candidate in combination[1:]:
            #     conjunction = conjunction & candidate
            #     # if not self.is_new_conjunction_valid(conjunction, con_list):
            #     #     valid = False
            #     # con_list.append(conjunction)
            conjunction: FandangoConstraintCandidate = build_conjunction(combination)
            if self.is_new_conjunction_valid(conjunction, combination):
                conjunction_candidates.add(conjunction)

        LOGGER.info("Found %s valid conjunctions", len(conjunction_candidates))
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
        self, candidate_set: CandidateSet
    ) -> List[Tuple[FandangoConstraintCandidate, ...]]:
        """
        Get all possible conjunctions of the candidate set with a maximum size of max_conjunction_size.
        """
        combinations = []
        sorted_candidates = sorted(candidate_set.candidates, key=lambda x: str(x))
        candidate_set_without_conjunctions = [
            candidate
            for candidate in sorted_candidates
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
            RecallThresholdValidation(min_recall=min_recall)
        )

    def process(self, candidates: CandidateSet) -> Set[FandangoConstraintCandidate]:
        """
        Iterates over all candidates to find the best disjunctions.
        :param candidates:
        :return: List of improved disjunction candidates
        """
        combinations = self.get_possible_disjunctions(candidates)

        disjunction_candidates = set()
        for combination in combinations:

            disjunction: FandangoConstraintCandidate = combination[0]
            # dis_list = [
            #     disjunction,
            # ]
            # valid = True
            for candidate in combination[1:]:
                disjunction = disjunction | candidate
                # if not self.is_new_disjunction_valid(disjunction, dis_list):
                #     valid = False
                # dis_list.append(disjunction)

            if self.is_new_disjunction_valid(disjunction, combination):
                print("Before:", [str(c) for c in combination])
                print(
                    "Adding disjunction: ",
                    disjunction,
                    " with precision: ",
                    disjunction.precision(),
                )
                disjunction_candidates.add(disjunction)

        LOGGER.info("Found %s valid disjunctions", len(disjunction_candidates))
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
        self, candidate_set: CandidateSet
    ) -> List[Tuple[FandangoConstraintCandidate, ...]]:
        """
        Get all possible disjunctions of the candidate set with a maximum size of max_disjunction_size.
        """
        combinations = []
        sorted_candidates = sorted(candidate_set.candidates, key=lambda x: str(x))

        candidate_set_without_disjunctions = [
            candidate
            for candidate in sorted_candidates
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


class RecallThresholdValidation(DisjunctionValidationStrategy):
    """
    Validates that the new disjunction's recall exceeds a minimum threshold.
    """

    def __init__(self, min_recall: float):
        self.min_recall = min_recall

    def is_valid(
        self,
        disjunction: FandangoConstraintCandidate,
        combination: Union[
            List[FandangoConstraintCandidate], Tuple[FandangoConstraintCandidate, ...]
        ],
        **kwargs,
    ) -> bool:
        new_recall = disjunction.recall()
        return new_recall > self.min_recall and all(
            new_recall > candidate.recall() for candidate in combination
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
