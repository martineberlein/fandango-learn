from debugging_benchmark.middle.middle import MiddleBenchmarkRepository

from fandango.language.parse import parse_file
from fandangoLearner.input import FandangoInput, OracleResult
from fandango.language.symbol import NonTerminal
from fandangoLearner.learner import FandangoLearner

import time

if __name__ == "__main__":
    programs = MiddleBenchmarkRepository().build()
    program = programs[0]  # Middle.1

    grammar, _ = parse_file("middle.fan")

    test_inputs = []
    for _ in range(100):
        inp = grammar.fuzz()
        test_inputs.append(str(inp))

    initial_inputs = {
        FandangoInput.from_str(grammar, inp, program.oracle(inp)[0]) for inp in program.get_initial_inputs() # + test_inputs
    }

    learner = FandangoLearner(grammar)
    relevant_non_terminals = {
        NonTerminal("<x>"),
        NonTerminal("<y>"),
        NonTerminal("<z>"),
    }

    start_time_learning = time.time()
    candidates = learner.learn_constraints(initial_inputs, relevant_non_terminals)
    end_time_learning = time.time()

    print(f"Time taken to learn constraints: {end_time_learning - start_time_learning:.4f} seconds")
    print("Best Constraints:")

    test_inputs = []
    for _ in range(4000):
        inp = grammar.fuzz()
        test_inputs.append((str(inp), program.oracle(str(inp))[0]))

    evaluation_inputs = {FandangoInput.from_str(grammar, inp, result) for inp, result in test_inputs}

    start_time = time.time()
    print("Evaluate Constraints with: ", len(evaluation_inputs), "inputs")
    for candidate in candidates:
        candidate.evaluate(evaluation_inputs)
        print("Constraint:", candidate.constraint, "Recall:", candidate.recall(), "Precision:", candidate.precision())
    print("\n")

    print("Time taken to evaluate constraints:", time.time() - start_time)

