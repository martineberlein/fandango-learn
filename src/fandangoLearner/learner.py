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

from .learning.candidate import FandangoConstraintCandidate
from .data.input import FandangoInput
from .logger import LOGGER
from .learning.combination import ConjunctionProcessor
from .core import BaseFandangoLearner


class FandangoLearner(BaseFandangoLearner):

    def __init__(
        self, grammar: Grammar, patterns: Optional[Iterable[str]] = None, **kwargs
    ):
        super().__init__(grammar, patterns, **kwargs)
        self.max_conjunction_size = 2
        self.positive_learning_size = 5

        self.conjunction_processor = ConjunctionProcessor(
            self.max_conjunction_size, self.min_precision, self.min_recall
        )

    def learn_constraints(
        self,
        test_inputs: Set[FandangoInput],
        relevant_non_terminals: Set[NonTerminal] = None,
        **kwargs,
    ) -> Optional[List[FandangoConstraintCandidate]]:

        if not relevant_non_terminals:
            relevant_non_terminals = set()
            for non_terminal in self.grammar:
                relevant_non_terminals.add(non_terminal)

        positive_inputs, negative_inputs = self.categorize_inputs(test_inputs)

        # Sort and Filter:
        positive_inputs = self.sort_and_filter_positive_inputs(positive_inputs)

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

        conjunction_candidates = self.conjunction_processor.process(self.candidates)
        self.candidates = self.candidates + conjunction_candidates

        return self.get_best_candidates()

    def sort_and_filter_positive_inputs(self, positive_inputs: Set[FandangoInput]):
        """
        This method is used to filter the positive inputs that are used for learning.
        :param positive_inputs:
        :return: the filtered positive inputs.
        """
        filtered_inputs = set(list(positive_inputs)[: self.positive_learning_size])
        LOGGER.info("Filtered positive inputs for learning: %s", len(filtered_inputs))
        return filtered_inputs

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
        relevant_non_terminals: Set[NonTerminal],
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
