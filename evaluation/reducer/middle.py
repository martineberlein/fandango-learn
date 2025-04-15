import time
from pathlib import Path
import random

from fdlearn.data import OracleResult
from fdlearn.interface.fandango import parse
from fdlearn.logger import LoggerLevel
from fdlearn.data.input import FandangoInput
from fdlearn.refinement.learner import FDLearnReducer

from debugging_benchmark.middle.middle import MiddleBenchmarkRepository
from evaluation.evaluation_helper import format_results


def evaluate_middle(logger_level=LoggerLevel.INFO, random_seed=1):
    random.seed(random_seed)
    filename = Path(__file__).resolve().parent.parent / "resources" / "middle.fan"
    grammar, _ = parse(filename)

    programs = MiddleBenchmarkRepository().build()
    program = programs[0]  # Middle.1

    def oracle(x):
        result = program.oracle(x)[0]
        if result.is_failing():
            return OracleResult.FAILING
        return OracleResult.PASSING

    initial_inputs = {
        FandangoInput.from_str(grammar, inp, oracle(inp)) for inp in program.get_initial_inputs()
    }

    start_time_learning = time.time()
    learner = FDLearnReducer(grammar,oracle=oracle, logger_level=logger_level)

    candidates = learner.learn_constraints(
        initial_inputs,
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
