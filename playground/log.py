import logging

from fandango.language.parse import parse
from fandango.logger import LOGGER
from fandango.constraints.base import *

from fandangoLearner.language.visitor import LoggingVisitor
from fandangoLearner.language.constraints import NegationConstraint
from fandangoLearner.language.transformer import NormalizationTransformer


def get_constraint(constraint):
    _, constraints = parse(constraint)
    return constraints[0]


if __name__ == "__main__":
    visitor = LoggingVisitor()

    comparison = ComparisonConstraint(Comparison.EQUAL, "x", "y")
    negation = NegationConstraint(comparison)

    # negation.accept(visitor)

    inner_implication = ImplicationConstraint(
        antecedent=ComparisonConstraint(Comparison.EQUAL, "x", "y"),
        consequent=ComparisonConstraint(Comparison.NOT_EQUAL, "a", "b"),
    )
    outer_implication = ImplicationConstraint(
        antecedent=inner_implication,
        consequent=ComparisonConstraint(Comparison.EQUAL, "z", "w"),
    )

    transformer = NormalizationTransformer()
    normalized = outer_implication.transform(transformer)

    print(normalized)
    normalized.accept(visitor)