import itertools

from fandango.constraints.base import ConjunctionConstraint, DisjunctionConstraint, ImplicationConstraint, \
    ExpressionConstraint, ComparisonConstraint
from fandango.constraints.base import Constraint, ExistsConstraint, ForallConstraint
from fandango.language.search import RuleSearch, NonTerminalSearch, AttributeSearch
from fandango.language.symbol import NonTerminal

from fdlearn.learning.instantiation import (
    ConstraintTransformer,
    ValueMap,
)
from fdlearn.data.input import FandangoInput


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

    def _visit_implication(self, constraint: ImplicationConstraint, **kwargs)-> list[ImplicationConstraint]:
        """
        Recursively visit the antecedent and consequent in an ImplicationConstraint.
        """
        transformed_constraint_antecedents = self.transform(constraint.antecedent, **kwargs)

        transformed_constraint_consequents = self.transform(constraint.consequent, **kwargs)

        results: list["ImplicationConstraint"] = []
        for antecedent in transformed_constraint_antecedents:
            for consequent in transformed_constraint_consequents:
                results.append(
                    ImplicationConstraint(antecedent=antecedent, consequent=consequent)
                )
        return results

    def _visit_comparison(self, constraint: ComparisonConstraint, **kwargs) -> list[ComparisonConstraint]:
        pass

    def _visit_expression(self, constraint: ExpressionConstraint, **kwargs) -> list[ExpressionConstraint]:
        pass