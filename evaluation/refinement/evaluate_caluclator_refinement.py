import math
import time
import random
import os

from fandango.language.symbol import NonTerminal

from fdlearn.data import OracleResult
from fdlearn.logger import LoggerLevel
from fdlearn.interface import parse
from fdlearn.refinement.core import FandangoRefinement
from evaluation.evaluation_helper import format_results

def calculator_oracle(inp):
    try:
        eval(
            str(inp),
            {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan},
        )
    except ValueError:
        return OracleResult.FAILING
    return OracleResult.PASSING


def evaluate_calculator_refinement(logger_level=LoggerLevel.CRITICAL, random_seed=1):
    random.seed(random_seed)
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "calculator.fan")
    grammar, _ = parse(filename)

    initial_inputs_strings = {
        ("sqrt(-900)", True),
        ("sqrt(-10)", True),
        ("sqrt(0)", False),
        # ("sqrt(-1)", True),
        ("sin(-900)", False),
        ("sqrt(2)", False),
        ("cos(10)", False),
    }
    # initial_inputs = ["cos(12)", "sqrt(-900)"],
    initial_inputs = {
        inp for inp, _ in initial_inputs_strings
    }

    relevant_non_terminals = {
        NonTerminal("<number>"),
        NonTerminal("<maybeminus>"),
        NonTerminal("<function>"),
    }

    start_time_learning = time.time()

    fandango_re = FandangoRefinement(
        grammar=grammar,
        oracle=calculator_oracle,
        initial_inputs=initial_inputs,
        relevant_non_terminals=None,
        logger_level=logger_level,
    )

    learned_constraints = fandango_re.explain()

    end_time_learning = time.time()

    # round time
    time_in_seconds = round(end_time_learning - start_time_learning, 4)
    return format_results(
        "CalculatorRE", grammar, calculator_oracle, learned_constraints, time_in_seconds
    )


if __name__ == "__main__":
    results = evaluate_calculator_refinement(LoggerLevel.INFO, random_seed=3)
    print("Required Time: ", results["time_in_seconds"], " seconds")
    constraints = results["candidates"]
    for constraint in constraints:
        print(constraint)
