from abc import ABC, abstractmethod
from itertools import product
from copy import deepcopy
from typing import List, Dict, Set, Iterable, Tuple, Callable, Type

from fandango.constraints.base import Constraint, ComparisonConstraint
from fandango.language.search import RuleSearch
from fandango.language.symbol import NonTerminal

from fandangoLearner.logger import LOGGER


class PatternProcessor:
    """
    Manages the instantiation of patterns by applying the appropriate PatternInstantiation class.
    """

    def __init__(self, patterns: Iterable[Constraint]):
        self.patterns = patterns
        self.instantiation_classes: List[PatternInstantiation] = [
            ComparisonPatternInstantiation(),
        ]

    def instantiate_patterns(
        self,
        relevant_non_terminals: Iterable[NonTerminal],
        value_map: Dict[str, Dict[NonTerminal, List[str]]],
    ) -> List[Constraint]:
        instantiated_patterns = []

        for pattern in self.patterns:
            for instantiation_class in self.instantiation_classes:
                if isinstance(pattern, instantiation_class.supported_pattern_type()):
                    instantiated_patterns.extend(
                        instantiation_class.instantiation(
                            [pattern], relevant_non_terminals, value_map
                        )
                    )
                else:
                    LOGGER.error(
                        f"Pattern type {type(pattern)} is not yet supported for instantiation."
                    )

        return instantiated_patterns


class PatternInstantiation(ABC):
    """
    Abstract base class for pattern instantiation.
    """

    @abstractmethod
    def supported_pattern_type(self) -> Type[Constraint]:
        """
        Returns the type of pattern this class supports for instantiation.
        """
        pass

    @abstractmethod
    def instantiation(
        self,
        patterns: Iterable[Constraint],
        relevant_non_terminals: Iterable[NonTerminal],
        value_maps: Dict[str, Dict[NonTerminal, List[str]]],
        **kwargs,
    ) -> List[Constraint]:
        """
        Perform instantiation of the given patterns using the provided values.

        Args:
            patterns (Iterable[Constraint]): Patterns to instantiate.
            relevant_non_terminals (Iterable[NonTerminal]): Non-terminals to instantiate.
            value_maps (Dict[NonTerminal, List[str]]): Values to instantiate non-terminals.
            **kwargs: Additional arguments for customization.

        Returns:
            List[Tuple[Constraint, NonTerminal]]: Instantiated patterns.
        """
        pass

    @abstractmethod
    def replace_non_terminals(
        self,
        initialized_patterns: Iterable[Constraint],
        non_terminal_values: Iterable[NonTerminal],
    ) -> List[Tuple[Constraint, Set[NonTerminal]]]:
        """
        Replace non-terminal placeholders with actual values.
        """
        pass

    @abstractmethod
    def replace_placeholders(
        self,
        initialized_patterns: List[Tuple[Constraint, Set[NonTerminal]]],
        placeholder: NonTerminal,
        values: Dict[NonTerminal, List[str]],
        format_value: Callable[[str], str],
    ) -> List[Tuple[Constraint, Set[NonTerminal]]]:
        """
        Replace placeholders with actual values.
        """
        pass


class ComparisonPatternInstantiation(PatternInstantiation):
    """
    Handles instantiation of patterns with placeholders and non-terminals.
    """

    def supported_pattern_type(self) -> Type[Constraint]:
        return ComparisonConstraint

    def instantiation(
        self,
        patterns: Iterable[Constraint],
        relevant_non_terminals: Iterable[NonTerminal],
        value_maps: Dict[str, Dict[NonTerminal, List[str]]],
        **kwargs,
    ) -> List[Constraint]:
        """
        Instantiates the given patterns with the provided non-terminal values.

        Args:
            patterns (Iterable[Constraint]): Patterns to instantiate.
            relevant_non_terminals (Iterable[NonTerminal]): Non-terminals to instantiate.
            value_maps (Dict[str, Dict[NonTerminal, List[str]]]): Values to instantiate non-terminals.
            **kwargs: Additional arguments for customization.

        Returns:
            List[Tuple[Constraint, NonTerminal]]: Instantiated patterns.
        """

        assert all(isinstance(pattern, ComparisonConstraint) for pattern in patterns)

        instantiated_patterns = self.replace_non_terminals(
            patterns, relevant_non_terminals
        )

        instantiated_patterns = self.replace_placeholders(
            instantiated_patterns,
            NonTerminal("<STRING>"),
            value_maps["string_values"],
            lambda x: f"'{x}'",
        )
        instantiated_patterns = self.replace_placeholders(
            instantiated_patterns,
            NonTerminal("<INTEGER>"),
            value_maps["int_values"],
            lambda x: x,
        )

        return [pattern for pattern, _ in instantiated_patterns]

    def replace_non_terminals(
        self,
        initialized_patterns: Iterable[Constraint],
        non_terminal_values: Iterable[NonTerminal],
    ) -> List[Tuple[Constraint, Set[NonTerminal]]]:
        """
        Replaces <NON_TERMINAL> placeholders with actual non-terminal values.

        Args:
            initialized_patterns (Iterable[Constraint]): Patterns with placeholders to replace.
            non_terminal_values (Iterable[NonTerminal]): Actual values for non-terminals.

        Returns:
            List[Tuple[Constraint, Set[NonTerminal]]]: Updated patterns with replaced values.
        """
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
        """
        Replaces placeholders like <STRING> or <INTEGER> with actual values.

        Args:
            initialized_patterns (List[Tuple[Constraint, Set[NonTerminal]]]): Patterns with placeholders.
            placeholder (NonTerminal): The placeholder symbol to replace.
            values (Dict[NonTerminal, List[str]]): Values to replace the placeholder with.
            format_value (Callable[[str], str]): A function to format the replacement value.

        Returns:
            List[Tuple[Constraint, Set[NonTerminal]]]: Updated patterns with replaced placeholders.
        """
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
