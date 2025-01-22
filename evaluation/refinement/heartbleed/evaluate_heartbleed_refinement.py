import time
import os
import random

from fandango.language.parse import parse_file
from fandango.language.symbol import NonTerminal
from fandangoLearner.learner import FandangoLearner
from fandangoLearner.data.input import FandangoInput
from fandangoLearner.logger import LoggerLevel
from fandangoLearner.refinement.core import FandangoRefinement

from evaluation.heartbleed.heartbeat import (
    initial_inputs as heartbleed_inputs,
    oracle_simple as oracle,
)
from evaluation.evaluation_helper import format_results


def evaluate_heartbleed_refinement(logger_level=LoggerLevel.INFO, random_seed=1):
    random.seed(random_seed)
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "heartbleed.fan")
    grammar, _ = parse_file(filename)

    initial_inputs = {
        FandangoInput.from_str(grammar, inp, oracle(inp)) for inp in heartbleed_inputs
    }

    relevant_non_terminals = {
        NonTerminal("<payload>"),
        NonTerminal("<payloadlength>"),
    }

    start_time_learning = time.time()
    fandango_re = FandangoRefinement(
        grammar=grammar,
        oracle=oracle,
        initial_inputs=heartbleed_inputs,
        relevant_non_terminals=relevant_non_terminals,
        logger_level=logger_level,
    )

    learned_constraints = fandango_re.explain()

    end_time_learning = time.time()

    # round time
    time_in_seconds = round(end_time_learning - start_time_learning, 4)
    return format_results(
        "HeartbleedRE", grammar, oracle, learned_constraints, time_in_seconds
    )


if __name__ == "__main__":
    random.seed(1)
    results = evaluate_heartbleed_refinement()
    print("Required Time: ", results["time_in_seconds"], " seconds" )
    constraints = results["candidates"]
    for constraint in constraints:
        print(constraint)
