import time
from pathlib import Path
import random

from debugging_benchmark.heartbleed.heartbleed import HeartbleedBenchmarkRepository

from fdlearn.data.input import FandangoInput
from fdlearn.data.oracle import OracleResult
from fdlearn.logger import LoggerLevel
from fdlearn.interface.fandango import parse
from fdlearn.reduction.reducer import DecisionTreeRelevanceLearner, RandomForestRelevanceLearner, SHAPRelevanceLearner

from fdlearn.refinement.learner import FDLearnReducer
from evaluation.evaluation_helper import format_results


def evaluate_heartbleed(logger_level=LoggerLevel.INFO, random_seed=1):
    random.seed(random_seed)
    filename = Path(__file__).resolve().parent.parent / "resources" / "heartbleed.fan"
    grammar, _ = parse(filename)

    program = HeartbleedBenchmarkRepository().build()[0]

    def oracle(x):
        result_ = program.oracle(x)
        result = result_[0] if isinstance(result_, (list, tuple)) else result_
        if result.is_failing():
            return OracleResult.FAILING
        if str(result) == "UNDEFINED":
            return OracleResult.UNDEFINED
        return OracleResult.PASSING

    initial_inputs = {
        FandangoInput.from_str(grammar, inp, oracle(inp)) for inp in program.get_initial_inputs()
    }

    reducer = SHAPRelevanceLearner(grammar)

    start_time_learning = time.time()
    learner = FDLearnReducer(grammar, oracle=oracle, reducer=reducer, logger_level=logger_level)

    candidates = learner.learn_constraints(initial_inputs)

    end_time_learning = time.time()

    # round time
    time_in_seconds = round(end_time_learning - start_time_learning, 4)
    return format_results("Heartbleed", grammar, oracle, candidates, time_in_seconds)


if __name__ == "__main__":
    random.seed(1)
    results = evaluate_heartbleed()
    print("Required Time: ", results["time_in_seconds"], " seconds")
    constraints = results["candidates"]
    print("#number of constraints: ", len(constraints))
    for constraint in constraints:
        print(constraint)
