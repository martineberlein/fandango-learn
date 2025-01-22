from abc import ABC, abstractmethod
from itertools import product
from copy import deepcopy
from typing import List, Dict, Set, Iterable, Tuple, Callable, Type

from fandango.constraints.base import *
from fandango.language.search import RuleSearch
from fandango.language.symbol import NonTerminal

from fandangoLearner.data.input import FandangoInput
from fandangoLearner.learning.candidate import FandangoConstraintCandidate
from fandangoLearner.logger import LOGGER


class ValueMaps:
    def __init__(self, relevant_non_terminals: Set[NonTerminal]):
        self.relevant_non_terminals = relevant_non_terminals
        self._string_values = {nt: set() for nt in self.relevant_non_terminals}
        self._int_values = {nt: set() for nt in self.relevant_non_terminals}


    def get_string_values(self, non_terminal: NonTerminal) -> Set[str]:
        return self._string_values[non_terminal]

    def get_int_values(self, non_terminal: NonTerminal) -> Set[int]:
        return self._int_values[non_terminal]

    def get_filtered_int_values(self) -> Dict[NonTerminal, Set[str]]:
        return self.calculate_filtered_int_values()

    @staticmethod
    def is_number(value: str) -> bool:
        """Check if the given string represents a number."""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def calculate_non_terminal_values(self, inputs: Set[FandangoInput]) -> Tuple[
        Dict[NonTerminal, Set[str]], Dict[NonTerminal, Set[float]]]:
        """Extracts and returns values associated with non-terminals."""

        for input_obj in inputs:
            for non_terminal in self.relevant_non_terminals:
                found_trees = input_obj.tree.find_all_trees(non_terminal)
                for tree in found_trees:
                    value = str(tree)
                    if self.is_number(value):
                        self._int_values[non_terminal].add(eval(value))
                    else:
                        self._string_values[non_terminal].add(value)

        return self._string_values, self._int_values

    def calculate_filtered_int_values(self) -> Dict[NonTerminal, Set[str]]:
        """Filters the value map to only include min and max values for non-terminals that have integer values."""
        reduced_int_values = {}
        for non_terminal, values in self._int_values.items():
            if values:
                min_val, max_val = min(values), max(values)
                reduced_int_values[non_terminal] = {min_val, max_val}
        return reduced_int_values


class PatternProcessor:
    """
    Manages the instantiation of patterns by applying the appropriate PatternInstantiation class.
    """

    def __init__(self, patterns: Iterable[Constraint]):
        self.patterns = patterns

    def instantiate_patterns(
        self,
        relevant_non_terminals: Set[NonTerminal],
        positive_inputs: Set[FandangoInput],
    ) -> Set[FandangoConstraintCandidate]:
        instantiated_patterns = []

        value_map = self.extract_non_terminal_values(
            relevant_non_terminals, positive_inputs
        )
        # TODO
        self.filter_value_map(value_map)

        # Replace non-terminal placeholders with actual non-terminals
        for pattern in self.patterns:
            transformer = NonTerminalPlaceholderTransformer(relevant_non_terminals)
            pattern.accept(transformer)
            transformed = transformer.results
            instantiated_patterns.extend(transformed)

        final_patterns = []
        # Replace value placeholders with actual values
        for pattern in instantiated_patterns:
            transformer = ValuePlaceholderTransformer(value_map, positive_inputs)
            pattern.accept(transformer)
            transformed = transformer.results
            final_patterns.extend(transformed)

        new_candidates = set()
        for pattern in final_patterns:
            new_candidates.add(FandangoConstraintCandidate(pattern))

        return new_candidates


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
            for replacements in itertools.product(
                self.relevant_non_terminals, repeat=len(matches)
            ):
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

        for bound_container_nonterm in self.relevant_non_terminals:
            new_search = RuleSearch(bound_container_nonterm)
            for transformed_statement in transformed_constraints:
                self.results.append(
                    ForallConstraint(
                        statement=transformed_statement,
                        bound=constraint.bound,
                        search=new_search,
                    )
                )

    def visit_exists_constraint(self, constraint: "ExistsConstraint"):
        """
        Recursively visit the statement inside an exists constraint.
        """
        constraint.statement.accept(self)
        transformed_constraints = self.results
        self.results = []  # Reset for independent processing

        for bound_container_nonterm in self.relevant_non_terminals:
            if isinstance(
                constraint.search, RuleSearch
            ) and constraint.search.symbol == NonTerminal("<NON_TERMINAL>"):
                new_search = RuleSearch(bound_container_nonterm)
            else:
                new_search = constraint.search
            for transformed_statement in transformed_constraints:
                self.results.append(
                    ExistsConstraint(
                        statement=transformed_statement,
                        bound=constraint.bound,
                        search=new_search,
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
                self.results.append(
                    ImplicationConstraint(antecedent=antecedent, consequent=consequent)
                )

    def visit_expression_constraint(self, constraint: "ExpressionConstraint"):
        """
        Expression constraints are returned as-is.
        """
        self.results.append(constraint)


class ValuePlaceholderTransformer(ConstraintVisitor):
    """
    A visitor for replacing placeholders like <STRING> or <INTEGER> in constraints with actual values.
    """

    def __init__(
        self,
        value_maps: Dict[str, Dict[NonTerminal, List[str]]],
        test_inputs: Set[FandangoInput],
    ):
        """
        Initialize the transformer with value maps for placeholders.

        Args:
            value_maps (Dict[str, Dict[NonTerminal, List[str]]]): Mapping of placeholders to their replacement values.
        """
        super().__init__()
        self.value_maps = value_maps
        self.results: List[Constraint] = []
        self.test_inputs: Set[FandangoInput] = test_inputs

    def do_continue(self, constraint: "Constraint") -> bool:
        return False

    def update_value_map(self, bound: NonTerminal, search: RuleSearch):
        """ """
        for type in self.value_maps.keys():
            # string, int
            if search in self.value_maps[type].keys():
                if isinstance(search, RuleSearch):
                    self.value_maps[type][bound] = self.value_maps[type][search.symbol]

    def remove_value_map(self, bound: NonTerminal):
        for type in self.value_maps.keys():
            if bound in self.value_maps[type].keys():
                del self.value_maps[type][bound]

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

        self.update_value_map(constraint.bound, constraint.search)
        constraint.statement.accept(self)
        self.remove_value_map(constraint.bound)
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
        self.update_value_map(constraint.bound, constraint.search)
        constraint.statement.accept(self)
        self.remove_value_map(constraint.bound)

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

        self.results.append(
            DisjunctionConstraint(constraints=all_transformed_constraints)
        )

    def visit_conjunction_constraint(self, constraint: "ConjunctionConstraint"):
        """
        Recursively visit each constraint in a ConjunctionConstraint.
        """
        all_transformed_constraints = []
        for sub_constraint in constraint.constraints:
            sub_constraint.accept(self)
            all_transformed_constraints.extend(self.results)
            self.results = []  # Reset after each sub-constraint

        self.results.append(
            ConjunctionConstraint(constraints=all_transformed_constraints)
        )

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
                self.results.append(
                    ImplicationConstraint(antecedent=antecedent, consequent=consequent)
                )

    def visit_expression_constraint(self, constraint: "ExpressionConstraint"):
        """
        Expression constraints are returned as-is.
        """
        self.results.append(constraint)

    def get_combinations(self,  constraint: Constraint, tree: DerivationTree,
        scope: Optional[Dict[NonTerminal, DerivationTree]] = None):
        nodes: List[List[Tuple[str, DerivationTree]]] = []
        for name, search in constraint.searches.items():
            if search.symbol == NonTerminal("<INTEGER>"):
                continue
            nodes.append(
                [(name, container) for container in search.find(tree, scope=scope)]
            )
        return itertools.product(*nodes)

    def evaluate_partial(self, constraint: "ComparisonConstraint"):
        """This function is used to evaluate the partial constraints"""
        results = set()
        for inp in self.test_inputs:
            scope = None
            for combination in self.get_combinations(constraint, inp.tree, scope):
                local_variables = constraint.local_variables.copy()
                local_variables.update(
                    {name: container.evaluate() for name, container in combination}
                )
                try:
                    left_result = eval(
                        constraint.left, constraint.global_variables, local_variables
                    )
                    results.add(str(left_result))
                except Exception as e:
                    e.add_note("Evaluation failed: " + constraint.left)
                    LOGGER.error(e)
                    continue
        return results

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

            non_terminals = {
                pattern.searches[key].symbol
                for key in pattern.searches.keys()
                if key not in matches
            }
            if matches:
                if isinstance(pattern, ComparisonConstraint):
                    for non_terminal in non_terminals:

                        vals = set(values.get(non_terminal, []))
                        vals.update(self.evaluate_partial(pattern))

                        for value in vals:
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
