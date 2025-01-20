import time
import os
import random

from fandango.language.parse import parse_file
from fandango.language.symbol import NonTerminal
from fandangoLearner.learner import FandangoLearner
from fandangoLearner.logger import LoggerLevel

from debugging_benchmark.middle.middle import MiddleBenchmarkRepository
from evaluation.evaluation_helper import (
    get_inputs, format_results
)


def evaluate_middle(logger_level=LoggerLevel.INFO):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'middle.fan')
    grammar, _ = parse_file(filename)

    programs = MiddleBenchmarkRepository().build()
    program = programs[0]  # Middle.1

    # initial_inputs_failing, initial_inputs_passing = get_inputs(
    #     grammar,
    #     lambda x: program.oracle(x)[0],
    # )
    initial_inputs = set(program.get_initial_inputs())

    relevant_non_terminals = {
        NonTerminal("<x>"),
        NonTerminal("<y>"),
        NonTerminal("<z>"),
    }

    start_time_learning = time.time()
    learner = FandangoLearner(grammar, logger_level=logger_level)

    candidates = learner.learn_constraints(initial_inputs, relevant_non_terminals, oracle=lambda x: program.oracle(x)[0],)

    end_time_learning = time.time()

    # round time
    time_in_seconds = round(end_time_learning - start_time_learning, 4)
    return format_results(
        "Middle",
        grammar,
        lambda x: program.oracle(x)[0],
        candidates,
        time_in_seconds
    )


if __name__ == "__main__":
    random.seed(1)
    results = evaluate_middle()
    print("Required Time: ", results["time_in_seconds"], " seconds" )
    constraints = results["candidates"]
    for constraint in constraints:
        print(constraint)