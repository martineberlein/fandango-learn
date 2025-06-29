from pathlib import Path

from fandango.constraints.base import (
    ConstraintVisitor,
    Constraint,
    ExpressionConstraint,
    ComparisonConstraint,
)
from fandango.language import NonTerminal

TEST_ROOT = Path(__file__).parent
RESOURCES_ROOT = TEST_ROOT / "resources"
PROJECT_ROOT = TEST_ROOT.parent

PLACEHOLDERS = [
    NonTerminal("<INTEGER>"),
    NonTerminal("<STRING>"),
    NonTerminal("<NON_TERMINAL>"),
    NonTerminal("<ATTRIBUTE>"),
]


class PlaceholderVisitor(ConstraintVisitor):
    """
    A visitor that checks if a constraint contains any of the placeholders.
    """

    def __init__(self, placeholders=None, **kwargs):
        super().__init__()
        if placeholders is None:
            self.placeholders = PLACEHOLDERS

    def check_for_placeholders(self, constraint: Constraint) -> bool:
        """
        Checks if the constraint contains any of the placeholders.
        :param constraint:
        :return: True if the constraint contains any of the placeholders, False otherwise.
        """
        for _, search in constraint.searches.items():
            nt = search.get_access_points()
            print(nt)
            return any(n in self.placeholders for n in nt)
        return False

    def visit_expression_constraint(self, constraint: "ExpressionConstraint"):
        """Visits an expression constraint."""
        if self.check_for_placeholders(constraint):
            raise AssertionError()

    def visit_comparison_constraint(self, constraint: "ComparisonConstraint"):
        """Visits a comparison constraint."""
        if self.check_for_placeholders(constraint):
            raise AssertionError()
