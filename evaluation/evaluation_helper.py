from typing import List, Callable, Set
import time

from fandangoLearner.learning.candidate import FandangoConstraintCandidate
from fandangoLearner.data.input import FandangoInput


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
    evaluation_inputs = []
    for _ in range(num_inputs):
        inp = grammar.fuzz()
        evaluation_inputs.append((str(inp), oracle(str(inp))))

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
