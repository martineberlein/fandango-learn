from fandango.constraints.base import *

from fandangoLearner.language.constraints import NegationConstraint


class NormalizationTransformer(ConstraintTransformer):
    """
    A transformer to normalize constraints into a canonical form.
    Example transformations: Implications (A -> B) are converted to disjunctions (~A or B).
    Redundant conjunctions or disjunctions are simplified.
    """

    def transform_expression_constraint(self, constraint: "ExpressionConstraint") -> "ExpressionConstraint":
        # ExpressionConstraints are returned as-is.
        return constraint

    def transform_comparison_constraint(self, constraint: "ComparisonConstraint") -> "ComparisonConstraint":
        # ComparisonConstraints do not require normalization.
        return constraint

    def transform_forall_constraint(self, constraint: "ForallConstraint") -> "ForallConstraint":
        # Recursively normalize the inner statement.
        normalized_statement = constraint.statement.transform(self)
        return ForallConstraint(
            statement=normalized_statement, bound=constraint.bound, search=constraint.search
        )

    def transform_exists_constraint(self, constraint: "ExistsConstraint") -> "ExistsConstraint":
        # Recursively normalize the inner statement.
        normalized_statement = constraint.statement.transform(self)
        return ExistsConstraint(
            statement=normalized_statement, bound=constraint.bound, search=constraint.search
        )

    def transform_disjunction_constraint(self, constraint: "DisjunctionConstraint") -> "DisjunctionConstraint":
        # Recursively normalize each disjunct.
        normalized_constraints = [c.transform(self) for c in constraint.constraints]
        return DisjunctionConstraint(constraints=normalized_constraints)

    def transform_conjunction_constraint(self, constraint: "ConjunctionConstraint") -> "ConjunctionConstraint":
        # Recursively normalize each conjunct.
        normalized_constraints = [c.transform(self) for c in constraint.constraints]
        return ConjunctionConstraint(constraints=normalized_constraints)

    def transform_implication_constraint(self, constraint: "ImplicationConstraint") -> "DisjunctionConstraint":
        # Transform the implication (A -> B) into a disjunction (~A or B).
        antecedent_negation = NegationConstraint(constraint.antecedent)
        consequent = constraint.consequent.transform(self)
        return DisjunctionConstraint(
            constraints=[antecedent_negation.transform(self), consequent]
        )