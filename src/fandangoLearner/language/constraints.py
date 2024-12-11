from fandango.constraints.base import *


class NegationConstraint(Constraint):
    """A constraint to represent logical negations."""
    def __init__(self, inner_constraint: Constraint, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inner_constraint = inner_constraint

    def fitness(
            self, tree: DerivationTree, scope: Optional[Dict[NonTerminal, DerivationTree]] = None
    ) -> ConstraintFitness:
        """
        Computes the fitness for the negation of the inner constraint.

        Negation logic:
            - If the inner constraint is fully satisfied, this constraint is fully unsatisfied.
            - If the inner constraint is fully unsatisfied, this constraint is fully satisfied.
            - Otherwise, the fitness is calculated as the negation of the inner fitness.
        """
        # Evaluate the fitness of the inner constraint
        inner_fitness = self.inner_constraint.fitness(tree, scope)

        # Negate the fitness results
        solved = inner_fitness.total - inner_fitness.solved
        total = inner_fitness.total
        success = not inner_fitness.success

        failing_trees = [
            FailingTree(tree=t.node, cause=self) for t in inner_fitness.failing_trees
        ]

        return ConstraintFitness(
            solved=solved,
            total=total,
            success=success,
            failing_trees=failing_trees,
        )

    def __repr__(self):
        return f"~({repr(self.inner_constraint)})"


    def accept(self, visitor: "ConstraintVisitor"):
        """Accepts a visitor to visit this constraint."""
        visitor.visit_negation_constraint(self)
        if visitor.do_continue(self):
            self.inner_constraint.accept(visitor)

    def transform(self, transformer: "ConstraintTransformer") -> "Constraint":
        """Transforms the negation constraint using the provided transformer."""
        # Apply the transformer to the inner constraint.
        normalized_inner = self.inner_constraint.transform(transformer)
        return NegationConstraint(normalized_inner)

