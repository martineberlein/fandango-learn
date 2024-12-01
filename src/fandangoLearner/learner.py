from typing import List, Dict, Iterable, Optional, Set, Tuple, Callable
from abc import ABC, abstractmethod
import re
from itertools import product

from debugging_framework.input.oracle import OracleResult
from fandango.language.grammar import Grammar
from fandango.language.parse import parse, parse_file
from fandangoLearner.input import FandangoInput, OracleResult
from fandango.language.symbol import NonTerminal
from fandangoLearner.candidate import FandangoConstraintCandidate

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


class FandangoStringPatternLearner(BaseFandangoLearner):

    def learn_constraints(
        self, test_inputs: Set[FandangoInput], relevant_non_terminals=None, **kwargs
    ) -> Optional[List[FandangoConstraintCandidate]]:

        positive_inputs, negative_inputs = self.categorize_inputs(test_inputs)
        assert all(inp.oracle == OracleResult.FAILING for inp in positive_inputs)
        assert all(inp.oracle == OracleResult.PASSING for inp in negative_inputs)

        extracted_values = self.extract_non_terminal_values(relevant_non_terminals, positive_inputs)

        patterns_with_non_terminals = self.replace_non_terminals(self.patterns, relevant_non_terminals)
        patterns_with_strings = self.replace_strings(patterns_with_non_terminals, extracted_values["string_values"])
        final_patterns = self.replace_integers(patterns_with_strings, extracted_values["int_values"])

        constraints = [parse(pattern)[1][0] for pattern in final_patterns if not re.search(r"<\?([A-Z_]+)>", pattern)]

        candidates = []
        for constraint in constraints:
            candidate = FandangoConstraintCandidate(constraint)
            candidate.evaluate(positive_inputs)
            if candidate.recall() >= 0.8:
                candidates.append(candidate)

        return candidates

    @staticmethod
    def replace_non_terminals(patterns: Set[str], non_terminal_values: Iterable[str]) -> List[Dict[str, List[str]]]:
        non_terminal_placeholder = re.compile(r"<\?NON_TERMINAL>")
        replaced_patterns = []
        for pattern in patterns:
            matches = non_terminal_placeholder.findall(pattern)
            if matches:
                for replacements in product(non_terminal_values, repeat=len(matches)):
                    updated_pattern = pattern
                    used_non_terminals = []
                    for replacement in replacements:
                        updated_pattern = updated_pattern.replace("<?NON_TERMINAL>", replacement, 1)
                        used_non_terminals.append(replacement)
                    replaced_patterns.append({"pattern": updated_pattern, "non_terminals": used_non_terminals})
            else:
                replaced_patterns.append({"pattern": pattern, "non_terminals": []})
        return replaced_patterns

    @staticmethod
    def replace_strings(patterns_with_non_terminals: List[Dict[str, List[str]]],
                        string_values: Dict[str, Iterable[str]]) -> List[Dict[str, List[str]]]:
        string_placeholder = re.compile(r"<\?STRING>")
        replaced_patterns = []
        for item in patterns_with_non_terminals:
            pattern, non_terminals = item["pattern"], item["non_terminals"]
            if string_placeholder.search(pattern):
                for non_terminal in non_terminals:
                    if non_terminal in string_values:
                        for string_value in string_values[non_terminal]:
                            updated_pattern = pattern.replace("<?STRING>", f'"{string_value}"', 1)
                            replaced_patterns.append({"pattern": updated_pattern, "non_terminals": non_terminals})
            else:
                replaced_patterns.append(item)
        return replaced_patterns

    @staticmethod
    def replace_integers(patterns_with_strings: List[Dict[str, List[str]]], int_values: Dict[str, Iterable[str]]) -> \
    List[str]:
        int_placeholder = re.compile(r"<\?INTEGER>")
        final_patterns = []
        for item in patterns_with_strings:
            pattern, non_terminals = item["pattern"], item["non_terminals"]
            if int_placeholder.search(pattern):
                for non_terminal in non_terminals:
                    if non_terminal in int_values:
                        for int_value in int_values[non_terminal]:
                            updated_pattern = pattern.replace("<?INTEGER>", int_value, 1)
                            final_patterns.append(updated_pattern)
            else:
                final_patterns.append(pattern)
        return final_patterns

    @staticmethod
    def is_number(value: str) -> bool:
        try:
            int(value)
            return True
        except ValueError:
            return False

    def extract_non_terminal_values(self, relevant_non_terminals: List[str], initial_inputs: Set[FandangoInput]) -> Dict[
        str, Dict[str, List[str]]]:
        string_values = {}
        int_values = {}
        for non_terminal in relevant_non_terminals:
            for inp in initial_inputs:
                found_trees = inp.tree.find_all_trees(NonTerminal(non_terminal))
                for tree in found_trees:
                    value = str(tree)
                    if self.is_number(value):
                        int_values.setdefault(non_terminal, []).append(value)
                    else:
                        string_values.setdefault(non_terminal, []).append(value)
        return {
            "string_values": {k: list(set(v)) for k, v in string_values.items()},
            "int_values": {k: list(set(v)) for k, v in int_values.items()},
        }