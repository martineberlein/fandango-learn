class UniversalQuantifierTransformer(ConstraintTransformer):
    """
    A transformer that converts comparison constraints into universally quantified forall constraints.
    """

    def __init__(self):
        super().__init__()

    def transform_expression_constraint(self, constraint: "ExpressionConstraint") -> "ExpressionConstraint":
        """
        Expression constraints do not need transformation; return as-is.
        """
        return constraint

    def transform_comparison_constraint(self, constraint: "ComparisonConstraint") -> "Constraint":
        """
        Transform a comparison constraint into nested forall constraints.
        """
        # Extract non-terminal placeholders from the comparison's searches
        placeholders = {
            key: search.symbol
            for key, search in constraint.searches.items()
            if isinstance(search.symbol, NonTerminal)
        }

        # Start with the innermost constraint
        transformed_constraint = constraint
        for container, placeholder in reversed(list(placeholders.items())):
            transformed_constraint = ForallConstraint(
                statement=transformed_constraint,
                bound=NonTerminal(f"<container_{container}>"),
                search=RuleSearch(placeholder),
            )
        return transformed_constraint

    def transform_forall_constraint(self, constraint: "ForallConstraint") -> "ForallConstraint":
        """
        Recursively transform the statement inside a forall constraint.
        """
        transformed_statement = constraint.statement.transform(self)
        return ForallConstraint(
            statement=transformed_statement, bound=constraint.bound, search=constraint.search
        )

    def transform_exists_constraint(self, constraint: "ExistsConstraint") -> "ExistsConstraint":
        """
        Recursively transform the statement inside an exists constraint.
        """
        transformed_statement = constraint.statement.transform(self)
        return ExistsConstraint(
            statement=transformed_statement, bound=constraint.bound, search=constraint.search
        )

    def transform_disjunction_constraint(self, constraint: "DisjunctionConstraint") -> "DisjunctionConstraint":
        """
        Recursively transform each component of a disjunction.
        """
        transformed_constraints = [c.transform(self) for c in constraint.constraints]
        return DisjunctionConstraint(constraints=transformed_constraints)

    def transform_conjunction_constraint(self, constraint: "ConjunctionConstraint") -> "ConjunctionConstraint":
        """
        Recursively transform each component of a conjunction.
        """
        transformed_constraints = [c.transform(self) for c in constraint.constraints]
        return ConjunctionConstraint(constraints=transformed_constraints)

    def transform_implication_constraint(self, constraint: "ImplicationConstraint") -> "ImplicationConstraint":
        """
        Recursively transform both the antecedent and consequent of an implication.
        """
        transformed_antecedent = constraint.antecedent.transform(self)
        transformed_consequent = constraint.consequent.transform(self)
        return ImplicationConstraint(
            antecedent=transformed_antecedent, consequent=transformed_consequent
        )