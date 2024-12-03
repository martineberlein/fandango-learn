import time

from fandango.language.parse import parse_file
from fandango.language.symbol import NonTerminal
from fandangoLearner.learner import FandangoLearner

from debugging_benchmark.middle.middle import MiddleBenchmarkRepository
from evaluation_helper import evaluate_candidates, get_inputs, print_constraints


if __name__ == "__main__":
    grammar, _ = parse_file("middle.fan")

    programs = MiddleBenchmarkRepository().build()
    program = programs[0]  # Middle.1

    # initial_inputs = {
    #     FandangoInput.from_str(grammar, inp, program.oracle(inp)[0])
    #     for inp in program.get_initial_inputs()
    # }

    initial_inputs_failing, initial_inputs_passing = get_inputs(grammar, lambda x: program.oracle(x)[0])
    initial_inputs = initial_inputs_failing.union(initial_inputs_passing)

    relevant_non_terminals = {
        NonTerminal("<x>"),
        NonTerminal("<y>"),
        NonTerminal("<z>"),
    }

    start_time_learning = time.time()
    learner = FandangoLearner(grammar)
    candidates = learner.learn_constraints(initial_inputs, relevant_non_terminals)
    end_time_learning = time.time()

    print(f"Time taken to learn constraints: {end_time_learning - start_time_learning:.4f} seconds", end="\n\n")

    print_constraints(candidates, initial_inputs)

    print()
    evaluate_candidates(candidates, grammar, lambda x: program.oracle(x)[0])