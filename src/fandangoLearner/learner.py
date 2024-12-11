from typing import List, Dict, Iterable, Optional, Set, Tuple, Callable, Any
from itertools import product
from copy import deepcopy

from fandango.language.grammar import Grammar
from fandango.language.symbol import NonTerminal
from fandango.constraints.base import (
    Constraint,
    ComparisonConstraint,
)
from fandango.language.search import RuleSearch
from debugging_framework.input.oracle import OracleResult

from .learning.candidate import FandangoConstraintCandidate
from .data.input import FandangoInput
from .logger import LOGGER
from .learning.combination import ConjunctionProcessor, DisjunctionProcessor
from .learning.instantiation import PatternProcessor
from .core import BaseFandangoLearner


class FandangoLearner(BaseFandangoLearner):
    """
    A candidate learner that learns fandango constraints based on patterns from a pattern repository.
    """

    def __init__(
        self, grammar: Grammar, patterns: Optional[Iterable[str]] = None, **kwargs
    ):
        """
        Initializes the FandangoLearner with a grammar and optional patterns.

        Args:
            grammar (Grammar): The grammar used for parsing and learning constraints.
            patterns (Optional[Iterable[str]]): A collection of patterns to be used in the learning process.
            **kwargs: Additional arguments for customization.
        """
        super().__init__(grammar, patterns, **kwargs)
        self.max_conjunction_size = 2
        self.max_disjunction_size = 2
        self.positive_learning_size = 5

        self.pattern_processor = PatternProcessor(self.patterns)

        self.conjunction_processor = ConjunctionProcessor(
            self.max_conjunction_size, self.min_precision, self.min_recall
        )
        self.disjunction_processor = DisjunctionProcessor(
            self.max_disjunction_size, self.min_precision, self.min_recall
        )

    def learn_constraints(
        self,
        test_inputs: set[FandangoInput] | set[str],
        relevant_non_terminals: Set[NonTerminal] = None,
        oracle: Callable[[str], OracleResult] = None,
        **kwargs,
    ) -> Optional[List[FandangoConstraintCandidate]]:
        """
        Learns constraints based on the provided test inputs and grammar patterns.

        Args:
            test_inputs (Set[FandangoInput]): A set of test inputs used for learning constraints.
            relevant_non_terminals (Set[NonTerminal], optional): A set of non-terminals relevant for learning.
            **kwargs: Additional arguments for learning customization.

        Returns:
            Optional[List[FandangoConstraintCandidate]]: A list of learned constraint candidates or None.
        """
        if any(isinstance(inp, str) for inp in test_inputs):
            test_inputs = self.parse_string_initial_inputs(test_inputs, oracle)

        if not relevant_non_terminals:
            relevant_non_terminals = set(self.grammar)

        positive_inputs, negative_inputs = self.categorize_inputs(test_inputs)

        positive_inputs = self.sort_and_filter_positive_inputs(positive_inputs)

        value_maps = self.extract_non_terminal_values(
            relevant_non_terminals, positive_inputs
        )

        instantiated_patterns = self.pattern_processor.instantiate_patterns(
            relevant_non_terminals, value_maps
        )

        self.parse_candidates(instantiated_patterns, test_inputs)

        conjunction_candidates = self.conjunction_processor.process(self.candidates)
        self.candidates += conjunction_candidates

        disjunction_candidates = self.disjunction_processor.process(self.candidates)
        self.candidates += disjunction_candidates

        return self.get_best_candidates()

    def parse_string_initial_inputs(
        self, initial_inputs: Set[str], oracle: Callable[[str], OracleResult]
    ) -> Set[FandangoInput]:
        """
        Parses string inputs and generates FandangoInput objects.

        Args:
            initial_inputs (Set[str]): A set of string inputs.
            oracle (Callable[[str], OracleResult]): An oracle function to evaluate inputs.

        Returns:
            Set[FandangoInput]: A set of FandangoInput objects.
        """
        return {
            FandangoInput.from_str(self.grammar, inp, oracle=oracle(inp))
            for inp in initial_inputs
        }

    def sort_and_filter_positive_inputs(
        self, positive_inputs: Set[FandangoInput]
    ) -> Set[FandangoInput]:
        """
        Filters and sorts positive inputs for learning.

        Args:
            positive_inputs (Set[FandangoInput]): A set of positive inputs.

        Returns:
            Set[FandangoInput]: A filtered subset of positive inputs.
        """
        filtered_inputs = set(list(positive_inputs)[: self.positive_learning_size])
        LOGGER.info("Filtered positive inputs for learning: %s", len(filtered_inputs))
        return filtered_inputs

    def parse_candidates(
        self,
        instantiated_patterns: List[Constraint],
        test_inputs: Set[FandangoInput],
        pre_filter: bool = False,
    ) -> None:
        """
        Generates constraint candidates based on instantiated patterns and evaluates them.

        Args:
            instantiated_patterns (List[Constraint]): A list of instantiated patterns and their corresponding non-terminals.
            test_inputs (Set[FandangoInput]): A set of test inputs to evaluate candidates.
            pre_filter (bool):
        """
        for pattern in instantiated_patterns:
            candidate = FandangoConstraintCandidate(pattern)
            try:
                candidate.evaluate(test_inputs)
                if pre_filter:
                    if candidate.recall() >= self.min_recall:
                        self.candidates.append(candidate)
                else:
                    self.candidates.append(candidate)
            except Exception:
                continue

    def extract_non_terminal_values(
        self,
        relevant_non_terminals: Set[NonTerminal],
        initial_inputs: Set[FandangoInput],
    ) -> Dict[str, Dict[NonTerminal, List[str]]]:
        """
        Extracts values associated with non-terminals from initial inputs.

        Args:
            relevant_non_terminals (Set[NonTerminal]): A set of relevant non-terminals.
            initial_inputs (Set[FandangoInput]): A set of initial inputs to extract values from.

        Returns:
            Dict[str, Dict[NonTerminal, List[str]]]: Extracted string and integer values.
        """
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
