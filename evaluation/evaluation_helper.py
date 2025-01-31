import random
from typing import List, Callable, Set
import time

from debugging_framework.input.oracle import OracleResult

from fandangoLearner.learning.candidate import FandangoConstraintCandidate
from fandangoLearner.data.input import FandangoInput
from fandangoLearner.learning.metric import RecallPriorityFitness


def print_constraints(
    candidates: List[FandangoConstraintCandidate], initial_inputs: Set[FandangoInput]
):
    """
    Print the constraints.
    """
    failing_inputs = {inp for inp in initial_inputs if inp.oracle.is_failing()}
    print(
        f"Learned Fandango Constraints (based on {len(initial_inputs)} initial inputs ({len(failing_inputs)} failing)):"
    )
    for candidate in candidates:
        print(candidate)


def evaluate_candidates(
    candidates: List[FandangoConstraintCandidate], grammar, oracle, num_inputs=2000
):
    """
    Evaluate the candidates.
    """
    start_time = time.time()
    evaluation_inputs = generate_evaluation_inputs(grammar, oracle, num_inputs)

    for candidate in candidates:
        candidate.evaluate(evaluation_inputs)
    eval_time = time.time() - start_time

    print(
        "Evaluate Constraints with:",
        len(evaluation_inputs),
        "inputs",
        f"(Time taken: {eval_time:.4f} seconds)",
    )
    for candidate in candidates:
        print(candidate)


def generate_evaluation_inputs(grammar, oracle: Callable, num_inputs=2000):
    """
    Generate the evaluation inputs.
    """
    random.seed(1)
    evaluation_inputs = []
    for _ in range(num_inputs):
        inp = grammar.fuzz()
        oracle_result = oracle(str(inp))
        if oracle_result != OracleResult.UNDEFINED:
            evaluation_inputs.append((str(inp), oracle_result))

    return {
        FandangoInput.from_str(grammar, inp, result)
        for inp, result in evaluation_inputs
    }


def get_inputs(
    grammar, oracle: Callable, num_failing=5, num_passing=10
) -> (Set[FandangoInput], Set[FandangoInput]):
    """
    Get the inputs.
    """
    failing_inputs = set()
    passing_inputs = set()
    while len(failing_inputs) < num_failing or len(passing_inputs) < num_passing:
        tree = grammar.fuzz()
        inp = FandangoInput.from_str(grammar, str(tree), oracle(str(tree)))
        if inp.oracle.is_failing():
            failing_inputs.add(inp) if len(failing_inputs) < num_failing else None
        else:
            passing_inputs.add(inp) if len(passing_inputs) < num_passing else None

    return failing_inputs, passing_inputs


def format_results(
    name: str,
    grammar,
    oracle,
    candidates: List[FandangoConstraintCandidate],
    time_in_seconds: float,
    num_inputs=2000,
):
    sorting_strategy = RecallPriorityFitness()
    evaluation_inputs = generate_evaluation_inputs(grammar, oracle, num_inputs)

    candidates = candidates or []

    for candidate in candidates:
        candidate.reset()
        candidate.evaluate(evaluation_inputs)

    sorted_candidates = sorted(
        candidates,
        key=lambda c: sorting_strategy.evaluate(c),
        reverse=True,
    )
    best_candidate = [
        candidate
        for candidate in sorted_candidates
        if sorting_strategy.is_equal(candidate, sorted_candidates[0])
    ]

    return {
        "name": name,
        "candidates": candidates if candidates else None,
        "time_in_seconds": time_in_seconds,
        "best_candidates": best_candidate if candidates else None,
        "precision": best_candidate[0].precision() if candidates else None,
        "recall": best_candidate[0].recall() if candidates else None,
    }
