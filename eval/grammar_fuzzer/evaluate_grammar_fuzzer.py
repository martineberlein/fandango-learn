import time

from fandango.constraints.base import Constraint
from fandango.language.tree import DerivationTree
from fandango.evolution.algorithm import Fandango

from benchmarks.valid.xml.xml_evaluation import get_xml_subject
from benchmarks.valid.iban.iban_evaluation import get_iban_subject


def evaluate_generated_inputs(
    subject: tuple, solutions: list[DerivationTree]
) -> tuple[str, int, int, float, tuple[float, int, int], float, float]:
    grammar, initial_inputs, oracle, additional_param = subject
    coverage = grammar.compute_grammar_coverage(solutions, 4)

    valid = []
    for solution in solutions:
        if oracle(solution).is_failing():
            valid.append(solution)

    set_mean_length = sum(len(str(x)) for x in valid) / len(valid)
    set_medium_length = sorted(len(str(x)) for x in valid)[len(valid) // 2]
    valid_percentage = len(valid) / len(solutions) * 100
    return (
        "XML",
        len(solutions),
        len(valid),
        valid_percentage,
        coverage,
        set_mean_length,
        set_medium_length,
    )


def generate_inputs(
    grammar, constraints: list[Constraint] | None = None, seconds: int = 60
):
    if constraints is None:
        constraints = []

    solutions = []

    end_time = time.time() + seconds

    fand_gen = Fandango(grammar, constraints=constraints, max_nodes=200)
    for tree in fand_gen.generate():
        solutions.append(tree)
        print(tree)
        if time.time() >= end_time:
            break

    return solutions


def run_evaluation(subject: tuple, seconds: int = 60):
    # Subject is a tuple containing (grammar, initial_inputs, oracle, additional_param)
    grammar, initial_inputs, oracle, additional_param = subject
    return generate_inputs(grammar, seconds)


def evaluate():
    subjects = [
        get_xml_subject,
        get_iban_subject,
    ]

    for subject in subjects:
        subject_data = subject()
        solutions = run_evaluation(subject_data, seconds=10)
        print(evaluate_generated_inputs(subject_data, solutions))


if __name__ == "__main__":
    evaluate()
