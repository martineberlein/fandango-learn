from typing import List, Dict, Iterable, Optional, Set, Tuple, Callable, Any, Union
from abc import ABC, abstractmethod
from itertools import product
from copy import deepcopy
import itertools

from debugging_framework.input.oracle import OracleResult
from fandango.language.grammar import Grammar
from fandango.language.parse import parse
from fandango.language.symbol import NonTerminal
from fandango.constraints.base import (
    Constraint,
    ComparisonConstraint,
    ConjunctionConstraint,
)
from fandango.language.search import RuleSearch

from .candidate import ConstraintCandidate, FandangoConstraintCandidate
from .input import Input as TestInput, FandangoInput
from .metric import FitnessStrategy, RecallPriorityFitness


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

        self.candidates: List[FandangoConstraintCandidate] = []

    def parse_patterns(self, patterns):
        """
        Parse the patterns into constraints.
        """
        return {parse(pattern)[1][0] for pattern in patterns}

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

    @staticmethod
    def is_number(value: str) -> bool:
        try:
            int(value)
            return True
        except ValueError:
            return False


class FandangoLearner(BaseFandangoLearner):

    def __init__(
        self, grammar: Grammar, patterns: Optional[Iterable[str]] = None, **kwargs
    ):
        super().__init__(grammar, patterns, **kwargs)
        self.max_conjunction_size = 4

    def learn_constraints(
        self, test_inputs: Set[FandangoInput], relevant_non_terminals=None, **kwargs
    ) -> Optional[List[FandangoConstraintCandidate]]:

        positive_inputs, negative_inputs = self.categorize_inputs(test_inputs)

        extracted_values = self.extract_non_terminal_values(
            relevant_non_terminals, positive_inputs
        )

        instantiated_patterns = self.replace_non_terminals(
            self.patterns, relevant_non_terminals
        )
        instantiated_patterns = self.replace_placeholders(
            instantiated_patterns,
            NonTerminal("<STRING>"),
            extracted_values["string_values"],
            lambda x: f"'{x}'",
        )
        instantiated_patterns = self.replace_placeholders(
            instantiated_patterns,
            NonTerminal("<INTEGER>"),
            extracted_values["int_values"],
            lambda x: x,
        )
        self.generate_candidates(instantiated_patterns, test_inputs)
        self.get_conjunctions()

        return self.get_best_candidates()

    def generate_candidates(
        self, instantiated_patterns, test_inputs: Set[FandangoInput]
    ):
        """Generate constraint candidates based on the replaced patterns."""
        for pattern, _ in instantiated_patterns:
            candidate = FandangoConstraintCandidate(pattern)
            try:
                candidate.evaluate(test_inputs)
                if candidate.recall() >= self.min_recall:
                    self.candidates.append(candidate)
            except Exception:
                continue

    def extract_non_terminal_values(
        self,
        relevant_non_terminals: List[NonTerminal],
        initial_inputs: Set[FandangoInput],
    ):
        """Extract values associated with non-terminals from initial inputs."""
        string_values: Dict[NonTerminal, Set[str]] = {}
        int_values: Dict[NonTerminal, Set[str]] = {}

        for non_terminal in relevant_non_terminals:
            for inp in initial_inputs:
                found_trees = inp.tree.find_all_trees(non_terminal)
                for tree in found_trees:
                    value = str(tree)
                    if self.is_number(value):
                        int_values.setdefault(non_terminal, set()).add(value)
                    else:
                        string_values.setdefault(non_terminal, set()).add(value)

        return {
            "string_values": {k: list(v) for k, v in string_values.items()},
            "int_values": {k: list(v) for k, v in int_values.items()},
        }

    def replace_non_terminals(
        self,
        initialized_patterns: Set[Constraint],
        non_terminal_values: Iterable[NonTerminal],
    ) -> List[Tuple[Constraint, Set[NonTerminal]]]:
        """Replace <NON_TERMINAL> placeholders with actual non-terminal values."""
        replaced_patterns = []
        for pattern in initialized_patterns:
            matches = [
                key
                for key in pattern.searches.keys()
                if pattern.searches[key].symbol == NonTerminal("<NON_TERMINAL>")
            ]
            if matches:
                if isinstance(pattern, ComparisonConstraint):
                    for replacements in product(
                        non_terminal_values, repeat=len(matches)
                    ):
                        new_searches = deepcopy(pattern.searches)
                        for key, replacement in zip(matches, replacements):
                            new_searches[key] = RuleSearch(replacement)
                        new_pattern = ComparisonConstraint(
                            operator=pattern.operator,
                            left=pattern.left,
                            right=pattern.right,
                            searches=new_searches,
                            local_variables=pattern.local_variables,
                            global_variables=pattern.global_variables,
                        )
                        replaced_patterns.append((new_pattern, set(replacements)))
                else:
                    raise ValueError(
                        f"Only comparison constraints are supported. "
                        f"Constraint type {type(pattern)} is not yet supported."
                    )
            else:
                replaced_patterns.append((pattern, set()))

        return replaced_patterns

    def replace_placeholders(
        self,
        initialized_patterns: List[Tuple[Constraint, Set[NonTerminal]]],
        placeholder: NonTerminal,
        values: Dict[NonTerminal, List[str]],
        format_value: Callable[[str], str],
    ) -> List[Tuple[Constraint, Set[NonTerminal]]]:
        """Replace placeholders like <STRING> or <INTEGER> with actual values."""
        new_patterns = []
        for pattern, non_terminals in initialized_patterns:
            matches = [
                key
                for key in pattern.searches.keys()
                if pattern.searches[key].symbol == placeholder
            ]
            if matches:
                if isinstance(pattern, ComparisonConstraint):
                    for non_terminal in non_terminals:
                        for value in values.get(non_terminal, []):
                            updated_right = pattern.right
                            for match in matches:
                                updated_right = updated_right.replace(
                                    match, format_value(value), 1
                                )
                            new_searches = deepcopy(pattern.searches)
                            for match in matches:
                                del new_searches[match]
                            new_pattern = ComparisonConstraint(
                                operator=pattern.operator,
                                left=pattern.left,
                                right=updated_right,
                                searches=new_searches,
                                local_variables=pattern.local_variables,
                                global_variables=pattern.global_variables,
                            )
                            new_patterns.append((new_pattern, non_terminals))
                else:
                    raise ValueError(
                        f"Only comparison constraints are supported. "
                        f"Constraint type {type(pattern)} is not yet supported."
                    )
            else:
                new_patterns.append((pattern, non_terminals))

        return new_patterns

    def check_minimum_recall(
        self, candidates: Tuple[FandangoConstraintCandidate, ...]
    ) -> bool:
        """
        Check if the recall of the candidates in the combination is greater than the minimum
        """
        return all(candidate.recall() >= self.min_recall for candidate in candidates)

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

    def get_conjunctions(
        self,
    ):
        combinations = self.get_possible_conjunctions(self.candidates)
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
                self.candidates.append(conjunction)

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
