import time
import os
import math
import random

from evaluation.evaluation_helper import format_results
from fdlearn.learner import FandangoLearner, NonTerminal, FandangoInput
from fdlearn.logger import LoggerLevel
from fdlearn.interface.fandango import parse
from fdlearn.data import OracleResult


def calculator_oracle(inp):
    try:
        eval(
            str(inp),
            {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan},
        )
    except ValueError:
        return OracleResult.FAILING
    return OracleResult.PASSING


def evaluate_calculator(logger_level=LoggerLevel.INFO, random_seed=1):
    random.seed(random_seed)
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "calculator.fan")
    grammar, _ = parse(filename)

    initial_inputs = {
        ("sqrt(-900)", True),
        ("sqrt(-10)", True),
        ("sqrt(0)", False),
        # ("sqrt(-1)", True),
        ("sin(-900)", False),
        ("sqrt(2)", False),
        ("cos(10)", False),
    }
    initial_inputs = {
        FandangoInput.from_str(grammar, inp, oracle) for inp, oracle in initial_inputs
    }

    relevant_non_terminals = {
        NonTerminal("<number>"),
        NonTerminal("<maybeminus>"),
        NonTerminal("<function>"),
    }

    start_time_learning = time.time()
    learner = FandangoLearner(grammar, logger_level=logger_level)

    learned_constraints = learner.learn_constraints(
        initial_inputs, relevant_non_terminals=relevant_non_terminals
    )

    end_time_learning = time.time()

    # round time
    time_in_seconds = round(end_time_learning - start_time_learning, 4)
    return format_results(
        "Calculator", grammar, calculator_oracle, learned_constraints, time_in_seconds
    )


if __name__ == "__main__":
    results = evaluate_calculator(random_seed=1)
    print("Required Time: ", results["time_in_seconds"], " seconds")
    constraints = results["candidates"]
    for constraint in constraints:
        print(constraint)
