import time
import os
import random

from fdlearn.data import OracleResult
from fdlearn.interface.fandango import parse_file
from fandango.language.symbol import NonTerminal
from fdlearn.learner import FandangoLearner
from fdlearn.logger import LoggerLevel

from debugging_benchmark.middle.middle import MiddleBenchmarkRepository
from evaluation.evaluation_helper import format_results


def evaluate_middle(logger_level=LoggerLevel.INFO, random_seed=1):
    random.seed(random_seed)
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "middle.fan")
    grammar, _ = parse_file(filename)

    programs = MiddleBenchmarkRepository().build()
    program = programs[0]  # Middle.1

    def oracle(x):
        result = program.oracle(x)[0]
        if result.is_failing():
            return OracleResult.FAILING
        return OracleResult.PASSING

    initial_inputs = set(program.get_initial_inputs())

    relevant_non_terminals = {
        NonTerminal("<x>"),
        NonTerminal("<y>"),
        NonTerminal("<z>"),
    }

    start_time_learning = time.time()
    learner = FandangoLearner(grammar, logger_level=logger_level)

    candidates = learner.learn_constraints(
        initial_inputs,
        relevant_non_terminals,
        oracle=oracle,
    )

    end_time_learning = time.time()

    # round time
    time_in_seconds = round(end_time_learning - start_time_learning, 4)
    return format_results(
        "Middle", grammar, oracle, candidates, time_in_seconds
    )


if __name__ == "__main__":
    random.seed(1)
    results = evaluate_middle(LoggerLevel.INFO)
    print("Required Time: ", results["time_in_seconds"], " seconds")
    constraints = results["candidates"]
    for constraint in constraints:
        print(constraint)
