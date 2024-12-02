import time

from fandango.language.parse import parse_file
from fandangoLearner.input import FandangoInput, OracleResult
from fandango.language.symbol import NonTerminal
from fandangoLearner.learner import FandangoLearner


if __name__ == "__main__":
    grammar, _ = parse_file("calculator.fan")
    test_inputs = [
        ("sqrt(-900)", OracleResult.FAILING),
        ("sqrt(-1)", OracleResult.FAILING),
        ("sin(-900)", OracleResult.PASSING),
        ("sqrt(2)", OracleResult.PASSING),
        ("cos(10)", OracleResult.PASSING),
    ]

    initial_inputs = {
        FandangoInput.from_str(grammar, inp, result) for inp, result in test_inputs
    }

    patterns = [
        "int(<NON_TERMINAL>) <= <INTEGER>;",
        "int(<NON_TERMINAL>) == <INTEGER>;",
        "str(<NON_TERMINAL>) == <STRING>;",
        "int(<NON_TERMINAL>) == len(str(<NON_TERMINAL>));",
        "int(<NON_TERMINAL>) == int(<NON_TERMINAL>) * <INTEGER> * int(<NON_TERMINAL>) * <INTEGER>;",
    ]

    non_terminal_values = {
        NonTerminal("<number>"),
        NonTerminal("<maybeminus>"),
        NonTerminal("<function>"),
    }

    start_time = time.time()
    learner = FandangoLearner(grammar, patterns)
    end_time = time.time()
    print(f"Time taken to initialize learner: {end_time - start_time:.2f} seconds")

    start_time_learning = time.time()
    candidates = learner.learn_constraints(initial_inputs, non_terminal_values)
    end_time_learning = time.time()

    print(f"Time taken to learn constraints: {end_time_learning - start_time_learning:.4f} seconds")
    print("Filtered Learned Atomic Constraints:")
    for candidate in candidates:
        candidate.evaluate(initial_inputs)
        print(
            f"Constraint: {candidate.constraint}, Recall: {candidate.recall()}, Precision: {candidate.precision()}"
        )