from abc import ABC

from fandango.constraints.base import (
    Constraint,
    ComparisonConstraint,
    ExpressionConstraint,
    ForallConstraint,
    ExistsConstraint,
    ConjunctionConstraint,
    DisjunctionConstraint,
    ImplicationConstraint,
)


class ConstraintTransformer(ABC):

    def transform(self, constraint: "Constraint", **kwargs) -> list["Constraint"]:
        """
        Public entry point. Returns a flat list of all instantiated constraints.
        """
        if isinstance(constraint, ComparisonConstraint):
            print(kwargs)
            return self._visit_comparison(constraint, **kwargs)

        if isinstance(constraint, ExpressionConstraint):
            return self._visit_expression(constraint, **kwargs)

        if isinstance(constraint, ForallConstraint):
            return self._visit_forall(constraint, **kwargs)

        if isinstance(constraint, ExistsConstraint):
            return self._visit_exists(constraint, **kwargs)

        if isinstance(constraint, ConjunctionConstraint):
            return self._visit_conjunction(constraint, **kwargs)

        if isinstance(constraint, DisjunctionConstraint):
            return self._visit_disjunction(constraint, **kwargs)

        if isinstance(constraint, ImplicationConstraint):
            return self._visit_implication(constraint, **kwargs)

        return [constraint]

    def _visit_comparison(self, constraint: "ComparisonConstraint", **kwargs) -> list["Constraint"]:
        raise NotImplementedError()

    def _visit_expression(self, constraint, **kwargs):
        raise NotImplementedError()

    def _visit_forall(self, constraint, **kwargs):
        raise NotImplementedError()

    def _visit_exists(self, constraint, **kwargs):
        raise NotImplementedError()

    def _visit_conjunction(self, constraint, **kwargs):
        raise NotImplementedError()

    def _visit_implication(self, constraint, **kwargs):
        raise NotImplementedError()

    def _visit_disjunction(self, constraint, **kwargs):
        raise NotImplementedError()

