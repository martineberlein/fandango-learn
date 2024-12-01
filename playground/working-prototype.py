from fandangoLearner.learner import FandangoStringPatternLearner
from fandango.language.parse import parse, parse_file
from fandangoLearner.input import FandangoInput, OracleResult
from fandango.language.symbol import NonTerminal
from fandangoLearner.candidate import FandangoConstraintCandidate

import math


def calculator_oracle(inp):
    try:
        eval(
            str(inp), {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan}
        )
    except ValueError:
        return OracleResult.FAILING
    return OracleResult.PASSING


if __name__ == "__main__":
    grammar, _ = parse_file('calculator.fan')
    test_inputs = [
        ("sqrt(-900)", OracleResult.FAILING),
        ("sqrt(2)", OracleResult.PASSING),
        ("cos(10)", OracleResult.PASSING),
    ]
    for _ in range(200):
        inp = grammar.fuzz()
        test_inputs.append((str(inp), calculator_oracle(inp)))

    initial_inputs = {FandangoInput.from_str(grammar, inp, result) for inp, result in test_inputs}

    patterns = [
        "int(<?NON_TERMINAL>) <= <?INTEGER>;",
        "str(<?NON_TERMINAL>) == <?STRING>;",
        "int(<?NON_TERMINAL>) == len(str(<?NON_TERMINAL>));"
    ]

    learner = FandangoStringPatternLearner(
        grammar,
        patterns=patterns
    )
    filtered_candidates = learner.learn_constraints(
        initial_inputs,
        relevant_non_terminals=["<number>", "<maybeminus>", "<function>"]
    )

    print("Filtered Learned Atomic Constraints: ")
    for candidate in filtered_candidates:
        candidate.evaluate(initial_inputs)
        print("Constraint:", candidate.constraint, "Recall:", candidate.recall(), "Precision:", candidate.precision())
    print("\n")

