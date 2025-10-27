from abc import ABC, abstractmethod
import itertools
from typing import Optional

from fandango.constraints.base import (
    ConjunctionConstraint,
    DisjunctionConstraint,
    ImplicationConstraint,
    ExpressionConstraint,
    ComparisonConstraint,
)
from fandango.constraints.base import Constraint, ExistsConstraint, ForallConstraint
from fandango.language.search import (
    RuleSearch,
    NonTerminalSearch,
    AttributeSearch,
    Container,
    DescendantAttributeSearch,
)
from fandango.language.symbol import NonTerminal
from fandango.language.tree import DerivationTree

from fdlearn.learning.instantiation import (
    ConstraintTransformer,
)
from fdlearn.data.input import FandangoInput
from fdlearn.logger import LOGGER
from fdlearn.learning.value_map import ValueMap


from copy import deepcopy

# Assuming the class definitions from the user's prompt are loaded.
# (e.g., Constraint, ExpressionConstraint, ConjunctionConstraint, etc.)


def deep_copy_constraint(constraint: Constraint) -> Constraint:
    """
    Performs a deep copy of a constraint object, ensuring that caches are
    not carried over and the object is fully independent.

    :param constraint: The constraint object to copy.
    :return: A new, deeply copied constraint object.
    """
    # Use deepcopy for mutable collections of simple types or objects
    # that are known to be deepcopy-safe (like NonTerminalSearch).
    new_searches = deepcopy(constraint.searches)
    new_local_vars = deepcopy(constraint.local_variables)
    new_global_vars = constraint.global_variables

    common_kwargs = {
        "searches": new_searches,
        "local_variables": new_local_vars,
        "global_variables": new_global_vars,
    }

    # Handle composite constraints by recursively copying their children.
    if isinstance(constraint, ConjunctionConstraint):
        new_constraints = [deep_copy_constraint(c) for c in constraint.constraints]
        return ConjunctionConstraint(
            constraints=new_constraints, lazy=constraint.lazy, **common_kwargs
        )

    if isinstance(constraint, DisjunctionConstraint):
        new_constraints = [deep_copy_constraint(c) for c in constraint.constraints]
        return DisjunctionConstraint(
            constraints=new_constraints, lazy=constraint.lazy, **common_kwargs
        )

    if isinstance(constraint, ImplicationConstraint):
        new_antecedent = deep_copy_constraint(constraint.antecedent)
        new_consequent = deep_copy_constraint(constraint.consequent)
        return ImplicationConstraint(
            antecedent=new_antecedent, consequent=new_consequent, **common_kwargs
        )

    # Handle leaf constraints by creating new instances with copied values.
    if isinstance(constraint, ExpressionConstraint):
        return ExpressionConstraint(expression=constraint.expression, **common_kwargs)

    if isinstance(constraint, ComparisonConstraint):
        return ComparisonConstraint(
            operator=constraint.operator,
            left=constraint.left,
            right=constraint.right,
            **common_kwargs,
        )

    # Fallback for any other constraint types.
    raise TypeError(f"Deep copy not implemented for type {type(constraint).__name__}")


class ValuePlaceholderTransformer(ConstraintTransformer, ABC):

    def __init__(
        self,
        value_map: ValueMap,
        test_inputs: set[FandangoInput],
        use_partial_evaluation: bool = False,
    ):
        """
        Initialize the transformer with value maps for placeholders.

        Args:
            value_map: Mapping of placeholders to their replacement values.
        """
        super().__init__()
        self.value_maps: ValueMap = value_map
        self.test_inputs: set[FandangoInput] = test_inputs
        self.use_partial_evaluation = use_partial_evaluation

    @staticmethod
    def all_combinations(sequences: list[list]) -> list[list]:
        result = []
        for combo in itertools.product(*sequences):
            result.append(list(combo))
        return result

    @staticmethod
    @abstractmethod
    def update_value_map(bound: NonTerminal, constraint_search: NonTerminalSearch):
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def remove_value_map(bound: NonTerminal):
        raise NotImplementedError()

    @staticmethod
    def get_search_symbol(search: NonTerminalSearch) -> NonTerminal:
        """
        Return the symbol corresponding to the given search instance.
        :param search:
        :return:
        """
        assert (
            isinstance(search, RuleSearch)
            or isinstance(search, AttributeSearch)
            or isinstance(search, DescendantAttributeSearch)
        )
        symbol = search.get_access_points()
        return symbol[0]

    def transform_quantified_constraints(
        self, constraint, bounded_non_terminals=None, **kwargs
    ) -> list[Constraint]:
        if bounded_non_terminals is None:
            bounded_non_terminals = {}
        self.update_value_map(constraint.bound, constraint.search)
        bounded_non_terminals[constraint.bound] = self.get_search_symbol(
            constraint.search
        )

        transformed_constraints = self.transform(
            constraint.statement, bounded_non_terminals=bounded_non_terminals
        )

        self.remove_value_map(constraint.bound)
        del bounded_non_terminals[constraint.bound]
        return transformed_constraints

    def _visit_exists(
        self, constraint: "ExistsConstraint", bounded_non_terminals=None, **kwargs
    ) -> list["ExistsConstraint"]:

        transformed_constraints = self.transform_quantified_constraints(
            constraint, bounded_non_terminals, **kwargs
        )

        result: list["ExistsConstraint"] = []
        for c in transformed_constraints:
            result.append(
                ExistsConstraint(
                    statement=c,
                    bound=constraint.bound,
                    search=constraint.search,
                )
            )

        return result

    def _visit_forall(
        self, constraint: "ForallConstraint", bounded_non_terminals=None, **kwargs
    ) -> list["ForallConstraint"]:

        transformed_constraints = self.transform_quantified_constraints(
            constraint, bounded_non_terminals, **kwargs
        )

        result: list["ForallConstraint"] = []
        for c in transformed_constraints:
            result.append(
                ForallConstraint(
                    statement=c,
                    bound=constraint.bound,
                    search=constraint.search,
                )
            )

        return result

    def transform_combination_constraints(
        self, constraint, **kwargs
    ) -> list[list[Constraint]]:
        all_transformed_constraints: list[list[Constraint]] = list()
        for sub_constraint in constraint.constraints:
            transformed_sub_constraints = self.transform(sub_constraint, **kwargs)
            all_transformed_constraints.append(transformed_sub_constraints)

        all_sub_combinations = self.all_combinations(all_transformed_constraints)
        return all_sub_combinations

    def _visit_conjunction(self, constraint, **kwargs) -> list["ConjunctionConstraint"]:
        all_sub_constraints = self.transform_combination_constraints(
            constraint, **kwargs
        )
        results: list[ConjunctionConstraint] = []
        for sub_constraints in all_sub_constraints:
            results.append(ConjunctionConstraint(constraints=sub_constraints))

        return results

    def _visit_disjunction(self, constraint, **kwargs) -> list[DisjunctionConstraint]:
        all_sub_constraints = self.transform_combination_constraints(
            constraint, **kwargs
        )
        results: list[DisjunctionConstraint] = []
        for sub_constraints in all_sub_constraints:
            results.append(DisjunctionConstraint(constraints=sub_constraints))

        return results

    def _visit_implication(
        self, constraint: ImplicationConstraint, **kwargs
    ) -> list[ImplicationConstraint]:
        """
        Recursively visit the antecedent and consequent in an ImplicationConstraint.
        """
        transformed_constraint_antecedents = self.transform(
            constraint.antecedent, **kwargs
        )

        transformed_constraint_consequents = self.transform(
            constraint.consequent, **kwargs
        )

        results: list["ImplicationConstraint"] = []
        for antecedent in transformed_constraint_antecedents:
            for consequent in transformed_constraint_consequents:
                results.append(
                    ImplicationConstraint(antecedent=antecedent, consequent=consequent)
                )
        return results

    @staticmethod
    def find_placeholders(
        constraint: Constraint, placeholder: NonTerminal
    ) -> list[str]:
        """
        Returns all the identifiers of the placeholders in the search dictionary.
        :param constraint:
        :param placeholder:
        :return: Identifiers of the placeholders
        """
        matches = []
        for name, search in constraint.searches.items():
            if isinstance(search, RuleSearch):
                if search.symbol == placeholder:
                    matches.append(name)
        return matches

    @staticmethod
    def resolve_bounded_non_terminals_in_constraint(
        constraint: Constraint, bounded_non_terminals, **kwargs
    ) -> Constraint:
        if not bounded_non_terminals:
            return constraint

        for name, search in constraint.searches.items():
            nt = bounded_non_terminals.get(search.symbol, None)
            if not nt:
                continue
            if isinstance(search, AttributeSearch):
                search.base = RuleSearch(nt)
            elif isinstance(search, RuleSearch):
                search.symbol = RuleSearch(nt)
        return constraint

    @staticmethod
    def get_combinations_for_partial_evaluation(
        constraint: Constraint,
        tree: DerivationTree,
        scope: Optional[dict[NonTerminal, DerivationTree]] = None,
    ):
        nodes: list[list[tuple[str, Container]]] = []
        for name, search in constraint.searches.items():
            if search.get_access_points() in (
                [NonTerminal("<INTEGER>")],
                [NonTerminal("<STRING>")],
            ):
                continue
            nodes.append(
                [(name, container) for container in search.find(tree, scope=scope)]
            )
        return itertools.product(*nodes)

    @staticmethod
    def format_value(value) -> any:
        return str(value)

    def evaluate_partial_constraint(
        self, constraint: Constraint, bounded_non_terminals, **kwargs
    ) -> set:
        results = set()
        try:
            tmp_constraint = deep_copy_constraint(constraint)
        except TypeError as e:
            return set()

        try:
            constraint_wt_bounded_nt = self.resolve_bounded_non_terminals_in_constraint(
                tmp_constraint, bounded_non_terminals, **kwargs
            )
        except AttributeError:
            return set()
        assert isinstance(constraint_wt_bounded_nt, ComparisonConstraint)

        for inp in self.test_inputs:
            for combination in self.get_combinations_for_partial_evaluation(
                constraint_wt_bounded_nt, inp.tree, scope=None
            ):
                local_variables = constraint_wt_bounded_nt.local_variables.copy()
                local_variables.update(
                    {name: container.evaluate() for name, container in combination}
                )
                try:
                    left_result = eval(
                        constraint_wt_bounded_nt.left,
                        constraint_wt_bounded_nt.global_variables,
                        local_variables,
                    )
                    results.add(str(left_result))
                except Exception as e:
                    e.add_note("Evaluation failed: " + constraint_wt_bounded_nt.left)
                    LOGGER.debug(e)
                    continue

        return results

    def replace_placeholders(
        self,
        constraint: Constraint,
        bounded_non_terminals,
        placeholder: NonTerminal,
        value_map,
        **kwargs,
    ) -> tuple[list[tuple[str, list[str]]], bool]:

        assert placeholder in (NonTerminal("<INTEGER>"), NonTerminal("<STRING>"))

        new_replacements: list[tuple[str, list[str]]] = []

        matches = self.find_placeholders(constraint, placeholder)
        if not matches:
            return [], False
        assert (
            len(matches) == 1
        ), "More than one Value-Placeholder is not yet supported."

        non_terminals = set()
        for _, search in constraint.searches.items():
            nt: NonTerminal = self.get_search_symbol(search)
            if nt not in (NonTerminal("<INTEGER>"), NonTerminal("<STRING>")):
                non_terminals.add(nt)

        for non_terminal in non_terminals:
            possible_values = value_map.get(non_terminal, set())
            if self.use_partial_evaluation:
                partial_eval_results = self.evaluate_partial_constraint(
                    constraint, bounded_non_terminals
                )
                if len(partial_eval_results) < 10:
                    possible_values.update(partial_eval_results)

            for possible_value in possible_values:
                new_replacements.append((possible_value, matches))
                # updated_right = constraint.right
                # # replace placeholder in with actual value
                # for match in matches:
                #     updated_right = updated_right.replace(
                #         match, self.format_value(possible_value), 1
                #     )
                # # remove placeholder search id from searches
                # new_searches = deepcopy(constraint.searches)
                # for match in matches:
                #     del new_searches[match]

                # new_constraints.append(
                #     ComparisonConstraint(
                #         operator=constraint.operator,
                #         left=constraint.left,
                #         right=updated_right,
                #         searches=new_searches,
                #         local_variables=constraint.local_variables,
                #         global_variables=constraint.global_variables,
                #     )
                # )

        return new_replacements, True

    @abstractmethod
    def _visit_comparison(
        self, constraint: ComparisonConstraint, bounded_non_terminals=None, **kwargs
    ) -> list[ComparisonConstraint]:
        raise NotImplementedError()

    def _visit_expression(
        self, constraint: ExpressionConstraint, bounded_non_terminals=None, **kwargs
    ) -> list[ExpressionConstraint]:
        return [constraint]


class IntegerPlaceholderTransformer(ValuePlaceholderTransformer):

    def __init__(
        self,
        value_map: ValueMap,
        test_inputs: set[FandangoInput],
        use_partial_evaluation: bool = False,
        use_filtered_integer_values=True,
    ):
        super().__init__(value_map, test_inputs, use_partial_evaluation)
        self.use_filtered_integer_values = use_filtered_integer_values

    def update_value_map(self, bound: NonTerminal, search: RuleSearch):
        """Update the value map for the given bound with the search symbol."""
        if search.symbol in self.value_maps.numeric_values:
            self.value_maps.numeric_values[bound] = self.value_maps.numeric_values[
                search.symbol
            ]

    def remove_value_map(self, bound: NonTerminal):
        """Remove the value map for the given bound."""
        if bound in self.value_maps.numeric_values:
            del self.value_maps.numeric_values[bound]

    @staticmethod
    def format_value(value) -> any:
        """
        Format the value for string representation.
        This can be overridden in subclasses if needed.
        """
        return f"{int(value)}"

    def _visit_comparison(
        self, constraint: ComparisonConstraint, bounded_non_terminals=None, **kwargs
    ) -> list[ComparisonConstraint]:

        result: list[ComparisonConstraint] = []

        integer_values = (
            self.value_maps.filtered_numeric_values
            if self.use_filtered_integer_values
            else self.value_maps.numeric_values
        )

        new_replacements, found_pl = self.replace_placeholders(
            constraint,
            bounded_non_terminals,
            placeholder=NonTerminal("<INTEGER>"),
            value_map=integer_values,
        )

        if not new_replacements and not found_pl:
            # If no replacements were found, return the original constraint
            return [constraint]

        if not new_replacements and found_pl:
            # If only found placeholders but no replacements, return the original constraint
            return []

        for replacement in new_replacements:
            value, matches = replacement
            updated_right = constraint.right
            # replace placeholder in with actual value
            for match in matches:
                updated_right = updated_right.replace(
                    match, self.format_value(value), 1
                )
            # remove placeholder search id from searches
            new_searches = deepcopy(constraint.searches)
            for match in matches:
                del new_searches[match]

            result.append(
                ComparisonConstraint(
                    operator=constraint.operator,
                    left=constraint.left,
                    right=updated_right,
                    searches=new_searches,
                    local_variables=constraint.local_variables,
                    global_variables=constraint.global_variables,
                )
            )

        return result


class StringPlaceholderTransformer(ValuePlaceholderTransformer):

    def update_value_map(self, bound: NonTerminal, search: RuleSearch):
        """Update the value map for the given bound with the search symbol."""
        if search.symbol in self.value_maps.string_values:
            self.value_maps.string_values[bound] = self.value_maps.string_values[
                search.symbol
            ]

    def remove_value_map(self, bound: NonTerminal):
        """Remove the value map for the given bound."""
        if bound in self.value_maps.string_values:
            del self.value_maps.string_values[bound]

    @staticmethod
    def format_value(value) -> any:
        """
        Format the value for string representation.
        This can be overridden in subclasses if needed.
        """
        return f"'{str(value)}'"

    def _visit_comparison(
        self, constraint: ComparisonConstraint, bounded_non_terminals=None, **kwargs
    ) -> list[ComparisonConstraint]:

        result: list[ComparisonConstraint] = []

        new_replacements, found_pl = self.replace_placeholders(
            constraint,
            bounded_non_terminals,
            placeholder=NonTerminal("<STRING>"),
            value_map=self.value_maps.string_values,
        )

        if not new_replacements and not found_pl:
            # If no replacements were found, return the original constraint
            return [constraint]

        if not new_replacements and found_pl:
            # If only found placeholders but no replacements, return the original constraint
            return []

        for replacement in new_replacements:
            value, matches = replacement
            updated_right = constraint.right
            # replace placeholder in with actual value
            for match in matches:
                updated_right = updated_right.replace(
                    match, self.format_value(value), 1
                )
            # remove placeholder search id from searches
            new_searches = deepcopy(constraint.searches)
            for match in matches:
                del new_searches[match]

            result.append(
                ComparisonConstraint(
                    operator=constraint.operator,
                    left=constraint.left,
                    right=updated_right,
                    searches=new_searches,
                    local_variables=constraint.local_variables,
                    global_variables=constraint.global_variables,
                )
            )

        return result

    @staticmethod
    def escape_string(s):
        return s.encode("unicode_escape").decode("utf-8")

    def _visit_expression(
        self, constraint: ExpressionConstraint, bounded_non_terminals=None, **kwargs
    ) -> list[ExpressionConstraint]:

        result: list[ExpressionConstraint] = []

        new_replacements, found_pl = self.replace_placeholders(
            constraint,
            bounded_non_terminals,
            placeholder=NonTerminal("<STRING>"),
            value_map=self.value_maps.string_values,
        )

        if not new_replacements and not found_pl:
            # If no replacements were found, return the original constraint
            return [constraint]

        if not new_replacements and found_pl:
            # If only found placeholders but no replacements, return the original constraint
            return []

        for replacement in new_replacements:
            value, matches = replacement
            expression = constraint.expression
            # replace placeholder in with actual value
            for match in matches:
                expression = expression.replace(match, self.format_value(value), 1)
            # remove placeholder search id from searches
            new_searches = deepcopy(constraint.searches)
            for match in matches:
                del new_searches[match]

            result.append(
                ExpressionConstraint(
                    expression=expression,
                    searches=new_searches,
                    local_variables=constraint.local_variables,
                    global_variables=constraint.global_variables,
                )
            )

        return result
