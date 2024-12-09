from abc import ABC, abstractmethod
from itertools import product
from copy import deepcopy
from typing import List, Dict, Set, Iterable, Tuple, Callable, Type

from fandango.constraints.base import *
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


class ForallPatternInstantiation(PatternInstantiation):

    """
    Here we need recursive instantiation of patterns.
    Structure:

        forall container in search: statement;

    container: NonTerminal
    search: RuleSearch
    statement: Constraint, can also be a ForallConstraint or ExistsConstraint

    The container is evaluated with the scope and a list of trees as containers.


    Ideas:
        1. Never set the container, as this will just be the name of the container.
        2. The search will be the search for the container, that is, NonTerminal("<NON_TERMINAL>")
            2.1 This will be replaced with the actual NonTerminals.
            2.2 The search is only used to find the containers.
        3.
    """

    def supported_pattern_type(self) -> Type[Constraint]:
        return ForallConstraint


class NonTerminalPlaceholderTransformer(ConstraintVisitor):
    """
        A visitor for replacing non-terminal placeholders in constraints with relevant non-terminals.
        """

    def __init__(self, relevant_non_terminals: Set[NonTerminal]):
        """
        Initialize the visitor with the set of relevant non-terminals.

        Args:
            relevant_non_terminals (Set[NonTerminal]): Non-terminals to replace placeholders with.
        """
        super().__init__()
        self.relevant_non_terminals = relevant_non_terminals
        self.results: List[Constraint] = []  # Store transformed constraints

    def do_continue(self, constraint: "Constraint") -> bool:
        return False

    def visit_comparison_constraint(self, constraint: "ComparisonConstraint"):
        """
        Replace <NON_TERMINAL> placeholders in a ComparisonConstraint.
        """
        matches = [
            key
            for key in constraint.searches.keys()
            if constraint.searches[key].symbol == NonTerminal("<NON_TERMINAL>")
        ]
        if matches:
            for replacements in itertools.product(self.relevant_non_terminals, repeat=len(matches)):
                new_searches = deepcopy(constraint.searches)
                for key, replacement in zip(matches, replacements):
                    new_searches[key] = RuleSearch(replacement)
                new_constraint = ComparisonConstraint(
                    operator=constraint.operator,
                    left=constraint.left,
                    right=constraint.right,
                    searches=new_searches,
                    local_variables=constraint.local_variables,
                    global_variables=constraint.global_variables,
                )
                self.results.append(new_constraint)
        else:
            self.results.append(constraint)

    def visit_forall_constraint(self, constraint: "ForallConstraint"):
        """
        Recursively visit the statement inside a forall constraint.
        """
        constraint.statement.accept(self)
        transformed_constraints = self.results
        self.results = []  # Reset for independent processing

        for transformed_statement in transformed_constraints:
            self.results.append(
                ForallConstraint(
                    statement=transformed_statement,
                    bound=constraint.bound,
                    search=constraint.search,
                )
            )

    def visit_exists_constraint(self, constraint: "ExistsConstraint"):
        """
        Recursively visit the statement inside an exists constraint.
        """
        constraint.statement.accept(self)
        transformed_constraints = self.results
        self.results = []  # Reset for independent processing

        for transformed_statement in transformed_constraints:
            self.results.append(
                ExistsConstraint(
                    statement=transformed_statement,
                    bound=constraint.bound,
                    search=constraint.search,
                )
            )

    def visit_disjunction_constraint(self, constraint: "DisjunctionConstraint"):
        """
        Recursively visit each constraint in a disjunction.
        """
        raise NotImplementedError("Disjunctions are not yet supported.")

    def visit_conjunction_constraint(self, constraint: "ConjunctionConstraint"):
        """
        Recursively visit each constraint in a conjunction.
        """
        raise NotImplementedError("Conjunctions are not yet supported.")

    def visit_implication_constraint(self, constraint: "ImplicationConstraint"):
        """
        Recursively visit the antecedent and consequent in an implication.
        """
        constraint.antecedent.accept(self)
        transformed_antecedents = self.results
        self.results = []  # Reset after antecedent

        constraint.consequent.accept(self)
        transformed_consequents = self.results
        self.results = []  # Reset after consequent

        for antecedent in transformed_antecedents:
            for consequent in transformed_consequents:
                self.results.append(ImplicationConstraint(antecedent=antecedent, consequent=consequent))

    def visit_expression_constraint(self, constraint: "ExpressionConstraint"):
        """
        Expression constraints are returned as-is.
        """
        self.results.append(constraint)


class ValuePlaceholderTransformer(ConstraintVisitor):
    """
    A visitor for replacing placeholders like <STRING> or <INTEGER> in constraints with actual values.
    """

    def __init__(self, value_maps: Dict[str, Dict[NonTerminal, List[str]]]):
        """
        Initialize the transformer with value maps for placeholders.

        Args:
            value_maps (Dict[str, Dict[NonTerminal, List[str]]]): Mapping of placeholders to their replacement values.
        """
        super().__init__()
        self.value_maps = value_maps
        self.results: List[Constraint] = []

    def do_continue(self, constraint: "Constraint") -> bool:
        return False

    def visit_comparison_constraint(self, constraint: "ComparisonConstraint"):
        """
        Replace placeholders in a ComparisonConstraint with corresponding values.
        """
        instantiated_patterns = [(constraint, set())]
        # Replace <STRING> placeholders
        instantiated_patterns = self.replace_placeholders(
            instantiated_patterns,
            NonTerminal("<STRING>"),
            self.value_maps["string_values"],
            lambda x: f"'{x}'",
        )
        # Replace <INTEGER> placeholders
        instantiated_patterns = self.replace_placeholders(
            instantiated_patterns,
            NonTerminal("<INTEGER>"),
            self.value_maps["int_values"],
            lambda x: x,
        )

        self.results.extend([pattern for pattern, _ in instantiated_patterns])

    def visit_forall_constraint(self, constraint: "ForallConstraint"):
        """
        Recursively visit the statement inside a ForallConstraint.
        """
        scope = dict()

        transformed_constraints = []
        for container in constraint.search.find(None, scope=scope):  # Assuming a `None` tree for search
            updated_scope = deepcopy(scope) if scope else {}
            updated_scope[constraint.bound] = container.evaluate()

            # Visit the statement with the updated scope
            constraint.statement.accept(self, scope=updated_scope)
            transformed_constraints.extend(self.results)
            self.results = []  # Reset after processing each container
        constraint.statement.accept(self)
        transformed_constraints = self.results
        self.results = []  # Reset for independent processing

        for transformed_statement in transformed_constraints:
            self.results.append(
                ForallConstraint(
                    statement=transformed_statement,
                    bound=constraint.bound,
                    search=constraint.search,
                )
            )

    def visit_exists_constraint(self, constraint: "ExistsConstraint"):
        """
        Recursively visit the statement inside an ExistsConstraint.
        """
        constraint.statement.accept(self)
        transformed_constraints = self.results
        self.results = []  # Reset for independent processing

        for transformed_statement in transformed_constraints:
            self.results.append(
                ExistsConstraint(
                    statement=transformed_statement,
                    bound=constraint.bound,
                    search=constraint.search,
                )
            )

    def visit_disjunction_constraint(self, constraint: "DisjunctionConstraint"):
        """
        Recursively visit each constraint in a DisjunctionConstraint.
        """
        all_transformed_constraints = []
        for sub_constraint in constraint.constraints:
            sub_constraint.accept(self)
            all_transformed_constraints.extend(self.results)
            self.results = []  # Reset after each sub-constraint

        self.results.append(DisjunctionConstraint(constraints=all_transformed_constraints))

    def visit_conjunction_constraint(self, constraint: "ConjunctionConstraint"):
        """
        Recursively visit each constraint in a ConjunctionConstraint.
        """
        all_transformed_constraints = []
        for sub_constraint in constraint.constraints:
            sub_constraint.accept(self)
            all_transformed_constraints.extend(self.results)
            self.results = []  # Reset after each sub-constraint

        self.results.append(ConjunctionConstraint(constraints=all_transformed_constraints))

    def visit_implication_constraint(self, constraint: "ImplicationConstraint"):
        """
        Recursively visit the antecedent and consequent in an ImplicationConstraint.
        """
        constraint.antecedent.accept(self)
        transformed_antecedents = self.results
        self.results = []  # Reset after antecedent

        constraint.consequent.accept(self)
        transformed_consequents = self.results
        self.results = []  # Reset after consequent

        for antecedent in transformed_antecedents:
            for consequent in transformed_consequents:
                self.results.append(ImplicationConstraint(antecedent=antecedent, consequent=consequent))

    def visit_expression_constraint(self, constraint: "ExpressionConstraint"):
        """
        Expression constraints are returned as-is.
        """
        self.results.append(constraint)

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
            print("Pattern: ", pattern)
            matches = [
                key
                for key in pattern.searches.keys()
                if pattern.searches[key].symbol == placeholder
            ]

            non_terminals = {pattern.searches[key].symbol for key in pattern.searches.keys() if key not in matches}
            # print("Matches: ", matches)
            print("Non-terminals: ", non_terminals)
            if matches:
                if isinstance(pattern, ComparisonConstraint):
                    for non_terminal in non_terminals:
                        for key, item in pattern.searches.items():
                            print("Key: ", key)
                            print("Item: ", item)
                            print("Type: ", type(item))
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