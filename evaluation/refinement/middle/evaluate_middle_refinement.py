import time
import os
import random

from fandango.language.parse import parse_file
from fandango.language.symbol import NonTerminal
from fandangoLearner.refinement.core import FandangoRefinement
from fandangoLearner.logger import LoggerLevel

from debugging_benchmark.middle.middle import MiddleBenchmarkRepository
from evaluation.evaluation_helper import get_inputs, format_results


def evaluate_middle(logger_level=LoggerLevel.INFO):
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

    fandangoRE = FandangoRefinement(
        grammar=grammar,
        oracle=lambda x: program.oracle(x)[0],
        initial_inputs=initial_inputs,
        relevant_non_terminals=relevant_non_terminals,
    )

    start_time = time.time()
    const = fandangoRE.explain()
    print(f"Time taken: {time.time() - start_time}")
    for candidate in const:
        print(candidate)

    for inp in fandangoRE.learner.all_positive_inputs:
        print(inp)


if __name__ == "__main__":
    random.seed(1)
    evaluate_middle()

