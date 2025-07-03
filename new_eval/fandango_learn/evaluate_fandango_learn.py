import random
import time

from fandango.language import DerivationTree
from fdlearn.learner import FandangoLearner
from fdlearn.data.input import FandangoInput
from fdlearn.logger import LOGGER, LoggerLevel

from new_eval.grammar_fuzzer.evaluate_grammar_fuzzer import generate_inputs
from new_eval.subjects.xml.xml_evaluation import get_xml_subject
from new_eval.subjects.iban.iban_evaluation import get_iban_subject
from new_eval import row_print_averages


def evaluate_generated_inputs(subject: tuple, solutions: list[DerivationTree]) -> tuple[str, int, int, float, tuple[float, int, int], float, float]:
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
        additional_param["name"],
        len(solutions),
        len(valid),
        valid_percentage,
        coverage,
        set_mean_length,
        set_medium_length,
    )


def learn_invariants(grammar, initial_inputs, oracle, additional_param):
    fdlearn = FandangoLearner(
        grammar=grammar,
    )
    _ = fdlearn.learn_constraints(test_inputs=initial_inputs)
    return fdlearn.get_best_candidates()


def run_evaluation(subject: tuple, seconds:int=60):
    # Subject is a tuple containing (grammar, initial_inputs, oracle, additional_param)
    grammar, initial_inputs, oracle, additional_param = subject

    valid, invalid = set(), set()
    while len(valid) < 5:
        tree = grammar.fuzz()
        inp = str(tree)
        if oracle(inp).is_failing():
            valid.add(inp)
        else:
            invalid.add(inp)

    valid_inputs = [FandangoInput.from_str(grammar, inp, True) for inp in list(valid)[:100]]
    invalid_inputs = [FandangoInput.from_str(grammar, inp, False) for inp in list(invalid)[:100]]
    initial_inputs = set(valid_inputs + invalid_inputs)

    invariants = learn_invariants(grammar, initial_inputs, oracle, additional_param)
    best_invariant = invariants[0].constraint if invariants else None
    solutions = generate_inputs(grammar, constraints=[best_invariant], seconds=10)
    return solutions


def evaluate():
    random.seed(1)
    subjects = [
        get_xml_subject,
        get_iban_subject,
    ]

    for subject in subjects:
        subject_data = subject()
        solutions = run_evaluation(subject_data, seconds=60)
        results = evaluate_generated_inputs(subject_data, solutions)
        row_print_averages(results, write_to_file=False)

if __name__ == '__main__':
    evaluate()
