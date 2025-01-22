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


def evaluate_heartbleed(logger_level=LoggerLevel.INFO):
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
    fandangoRE = FandangoRefinement(
        grammar=grammar,
        oracle=oracle,
        initial_inputs=heartbleed_inputs,
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
    results = evaluate_heartbleed()
    # print("Required Time: ", results["time_in_seconds"], " seconds" )
    # onstraints = results["candidates"]
    # for constraint in constraints:
    #    print(constraint)
