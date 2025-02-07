from itertools import product

from fandango.constraints.base import ConjunctionConstraint, DisjunctionConstraint, ComparisonConstraint, Comparison

from fandangoLearner.language.constraints import NegationConstraint
from fandangoLearner.learning.candidate import FandangoConstraintCandidate
from fandangoLearner.interface import parse_constraint


def construct_negations(candidates: list[FandangoConstraintCandidate]):
    """
    Construct negations for the given candidates.
    :param List[Candidate] candidates: The candidates to construct negations for.
    :return:
    """
    result = []
    for candidate in candidates:
        if isinstance(candidate.constraint, ConjunctionConstraint):
            result.extend(construct_negations_from_conjunctions(candidate))
        elif isinstance(candidate.constraint, DisjunctionConstraint):
            result.extend(construct_negation_from_disjunction(candidate))
        elif isinstance(candidate.constraint, ComparisonConstraint):
            result.append(negate_comparison_constraint(candidate))
        else:
            result.append(FandangoConstraintCandidate(NegationConstraint(candidate.constraint)))

    return result


def construct_negations_from_conjunctions(candidate: FandangoConstraintCandidate):
    """
    Construct negations for the given candidates.
    :param FandangoConstraintCandidate candidate: The candidates to construct negations for.
    :return:
    """
    assert isinstance(candidate.constraint, ConjunctionConstraint)
    lst = candidate.constraint.constraints

    def negate(constraint):
        return NegationConstraint(constraint)

    results = [FandangoConstraintCandidate(ConjunctionConstraint(
        [negate(value) if bit else value for value, bit in zip(lst, combination)]))
        for combination in product([0, 1], repeat=len(lst))
        if any(combination)
    ]

    return results


def construct_negation_from_disjunction(candidate: FandangoConstraintCandidate):
    """
    Construct a single negation for each sub-constraint in a disjunction.
    :param FandangoConstraintCandidate candidate: The candidate disjunction to construct negations for.
    :return: A list of disjunctions with one sub-constraint negated at a time.
    """
    assert isinstance(candidate.constraint, DisjunctionConstraint)
    lst = candidate.constraint.constraints

    def negate(constraint):
        return NegationConstraint(constraint)

    # Create one negation at a time
    results = [
        FandangoConstraintCandidate(DisjunctionConstraint(
            [negate(value) if i == idx else value for idx, value in enumerate(lst)]
        ))
        for i in range(len(lst))
    ]

    return results


def negate_comparison_operator(operator: Comparison) -> Comparison:
    negation_map = {
        Comparison.EQUAL: Comparison.NOT_EQUAL,
        Comparison.NOT_EQUAL: Comparison.EQUAL,
        Comparison.GREATER: Comparison.LESS_EQUAL,
        Comparison.GREATER_EQUAL: Comparison.LESS,
        Comparison.LESS: Comparison.GREATER_EQUAL,
        Comparison.LESS_EQUAL: Comparison.GREATER,
    }
    return negation_map[operator]


def negate_comparison_constraint(candidate: FandangoConstraintCandidate) -> FandangoConstraintCandidate:
    assert isinstance(candidate.constraint, ComparisonConstraint)
    constraint = candidate.constraint
    negated_operator = negate_comparison_operator(constraint.operator)
    return FandangoConstraintCandidate(ComparisonConstraint(
        negated_operator,
        constraint.left,
        constraint.right,
        searches=constraint.searches,
        local_variables=constraint.local_variables,
        global_variables=constraint.global_variables,
    ))


if __name__ == "__main__":
    constraint_1 = parse_constraint("int(<number>) <= 0;")
    constraint_2 = parse_constraint("str(<function>) <= 'sqrt';")
    candidate_conjunction = FandangoConstraintCandidate(ConjunctionConstraint([constraint_1, constraint_2]))
    candidate_disjunction = FandangoConstraintCandidate(DisjunctionConstraint([constraint_1, constraint_2]))
    res = construct_negations_from_conjunctions(candidate_conjunction)
    for cand in res:
        print(cand.constraint)
    res = construct_negation_from_disjunction(candidate_disjunction)
    for cand in res:
        print(cand)

    print(negate_comparison_constraint(FandangoConstraintCandidate(constraint_1)))

    print(construct_negations([candidate_conjunction, candidate_disjunction]))