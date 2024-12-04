from fandango.language.parse import parse_file
from fandangoLearner.data.input import FandangoInput, OracleResult
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

    learner = FandangoLearner(grammar, patterns)
    learned_constraints = learner.learn_constraints(initial_inputs, non_terminal_values)

    for candidate in learned_constraints:
        candidate.evaluate(initial_inputs)
        print(
            f"Constraint: {candidate.constraint}, Recall: {candidate.recall()}, Precision: {candidate.precision()}"
        )