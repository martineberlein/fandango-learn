import time

from fandango.language.parse import parse_file
from fandangoLearner.input import FandangoInput, OracleResult
from fandango.language.symbol import NonTerminal
from fandangoLearner.learner import FandangoLearner

from calculator import calculator_oracle



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
    for _ in range(100):
        inp = grammar.fuzz()
        test_inputs.append((str(inp), calculator_oracle(inp)))

    initial_inputs = {FandangoInput.from_str(grammar, inp, result) for inp, result in test_inputs}

    # patterns = [
    #     "int(<NON_TERMINAL>) <= <INTEGER>;",
    #     "int(<NON_TERMINAL>) == <INTEGER>;",
    #     "str(<NON_TERMINAL>) == <STRING>;",
    #     "int(<NON_TERMINAL>) == len(str(<NON_TERMINAL>));",
    #     "int(<NON_TERMINAL>) == int(<NON_TERMINAL>) * <INTEGER> * int(<NON_TERMINAL>) * <INTEGER>;",
    # ]

    non_terminal_values = {
        NonTerminal("<number>"),
        NonTerminal("<maybeminus>"),
        NonTerminal("<function>"),
    }

    start_time = time.time()
    learner = FandangoLearner(grammar)
    end_time = time.time()
    print(f"Time taken to initialize learner: {end_time - start_time:.2f} seconds")

    start_time_learning = time.time()
    candidates = learner.learn_constraints(initial_inputs, non_terminal_values)
    end_time_learning = time.time()

    print(f"Time taken to learn constraints: {end_time_learning - start_time_learning:.4f} seconds")
    print("Best Constraints:")

    for _ in range(2000):
        inp = grammar.fuzz()
        test_inputs.append((str(inp), calculator_oracle(inp)))

    evaluation_inputs = {FandangoInput.from_str(grammar, inp, result) for inp, result in test_inputs}

    start_time = time.time()
    print("Evaluate Constraints with: ", len(evaluation_inputs), "inputs")
    for candidate in candidates:
        candidate.evaluate(evaluation_inputs)
        print("Constraint:", candidate.constraint, "Recall:", candidate.recall(), "Precision:", candidate.precision())
    print("\n")

    print("Time taken to evaluate constraints:", time.time() - start_time)
