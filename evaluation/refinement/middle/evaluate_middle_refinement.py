import time
import os
import random

from fandango.language.parse import parse_file
from fandango.language.symbol import NonTerminal
from fandangoLearner.refinement.core import FandangoRefinement
from fandangoLearner.logger import LoggerLevel

from debugging_benchmark.middle.middle import MiddleBenchmarkRepository
from evaluation.evaluation_helper import format_results


def evaluate_middle_refinement(logger_level=LoggerLevel.INFO, random_seed=1):
    random.seed(random_seed)
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "middle.fan")
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

    fandango_re = FandangoRefinement(
        grammar=grammar,
        oracle=lambda x: program.oracle(x)[0],
        initial_inputs=initial_inputs,
        relevant_non_terminals=relevant_non_terminals,
        logger_level=logger_level,
    )

    candidates = fandango_re.explain()

    end_time_learning = time.time()

    # round time
    time_in_seconds = round(end_time_learning - start_time_learning, 4)
    return format_results(
        "MiddleRE", grammar, lambda x: program.oracle(x)[0], candidates, time_in_seconds
    )


if __name__ == "__main__":
    results = evaluate_middle_refinement()
    print("Required Time: ", results["time_in_seconds"], " seconds")
    constraints = results["candidates"]
    for constraint in constraints:
        print(constraint)
