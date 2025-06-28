import itertools
from typing import Optional
from copy import deepcopy

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
)
from fandango.language.symbol import NonTerminal
from fandango.language.tree import DerivationTree

from fdlearn.learning.instantiation import (
    ConstraintTransformer,
    ValueMap,
)
from fdlearn.data.input import FandangoInput
from fdlearn.logger import LOGGER


class ValuePlaceholderTransformer(ConstraintTransformer):

    def __init__(
        self,
        value_map: ValueMap,
        test_inputs: set[FandangoInput],
    ):
        """
        Initialize the transformer with value maps for placeholders.

        Args:
            value_map: Mapping of placeholders to their replacement values.
        """
        super().__init__()
        self.value_maps: ValueMap = value_map
        self.test_inputs: set[FandangoInput] = test_inputs

    @staticmethod
    def all_combinations(sequences: list[list]) -> list[list]:
        result = []
        for combo in itertools.product(*sequences):
            result.append(list(combo))
        return result

    @staticmethod
    def update_value_map(bound: NonTerminal, constraint_search: NonTerminalSearch):
        raise NotImplementedError()

    @staticmethod
    def remove_value_map(bound: NonTerminal):
        raise NotImplementedError()

    @staticmethod
    def get_search_symbol(search: NonTerminalSearch) -> NonTerminal:
        """
        Return the symbol corresponding to the given search instance.
        :param search:
        :return:
        """
        assert isinstance(search, RuleSearch) or isinstance(search, AttributeSearch)
        symbol = search.get_access_points()
        return symbol[0]

    def transform_quantified_constraints(
        self, constraint, bounded_non_terminals=None, **kwargs
    ) -> list[Constraint]:
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
                NonTerminal("<INTEGER>"),
                NonTerminal("<STRING>"),
            ):
                continue
            nodes.append(
                [(name, container) for container in search.find(tree, scope=scope)]
            )
        return itertools.product(*nodes)

    @staticmethod
    def format_value(value) -> any:
        raise value

    def evaluate_partial_constraint(
        self, constraint, bounded_non_terminals, **kwargs
    ) -> set:
        results = set()
        try:
            tmp_constraint = deepcopy(constraint)
        except TypeError as e:
            return set()

        constraint_wt_bounded_nt = self.resolve_bounded_non_terminals_in_constraint(
            tmp_constraint, bounded_non_terminals, **kwargs
        )
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
                    e.add_note("Evaluation failed: " + constraint.left)
                    LOGGER.debug(e)
                    continue

        return results

    def replace_placeholders(
        self,
        constraint: Constraint,
        bounded_non_terminals,
        placeholder: NonTerminal,
        value_map,
        evaluate_partials: bool = True,
        **kwargs,
    ) -> list[tuple[str, dict[str, NonTerminalSearch]]]:

        new_replacements: list[tuple[str, dict[str, NonTerminalSearch]]] = []

        assert placeholder in (NonTerminal("<INTEGER>"), NonTerminal("<STRING>"))

        if not isinstance(constraint, ComparisonConstraint):
            raise ValueError(
                f"Only comparison constraints are supported. "
                f"Constraint type {type(constraint)} is not yet supported."
            )

        matches = self.find_placeholders(constraint, placeholder)
        if not matches:
            return []
        assert (
            len(matches) == 1
        ), "More than one Value-Placeholder is not yet supported."

        non_terminals = set()
        for _, search in constraint.searches.items():
            nt: NonTerminal = self.get_search_symbol(search)
            if nt not in (NonTerminal("<INTEGER>"), NonTerminal("<STRING>")):
                non_terminals.add(nt)

        for non_terminal in non_terminals:
            possible_values = value_map.get(non_terminal, [])
            if evaluate_partials:
                possible_values.update(
                    self.evaluate_partial_constraint(constraint, bounded_non_terminals)
                )

            for possible_value in possible_values:
                updated_right = constraint.right
                # replace placeholder in with actual value
                for match in matches:
                    updated_right = updated_right.replace(
                        match, self.format_value(possible_value), 1
                    )
                # remove placeholder search id from searches
                new_searches = deepcopy(constraint.searches)
                for match in matches:
                    del new_searches[match]

                new_replacements.append((updated_right, new_searches))

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

        return new_replacements

    def _visit_comparison(
        self, constraint: ComparisonConstraint, bounded_non_terminals=None, **kwargs
    ) -> list[ComparisonConstraint]:
        raise NotImplementedError()

    def _visit_expression(
        self, constraint: ExpressionConstraint, bounded_non_terminals=None, **kwargs
    ) -> list[ExpressionConstraint]:
        return [constraint]
