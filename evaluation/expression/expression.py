import os
import time
import random

from fandango.language.parse import parse_file
from islearn.learner import InvariantLearner
from evaluation.heartbleed.heartbeat import initial_inputs
from fandangoLearner.learner import FandangoLearner, NonTerminal, FandangoInput
from fandangoLearner.logger import LoggerLevel
from fandangoLearner.resources.patterns import Pattern

from debugging_benchmark.expression.expression import ExpressionBenchmarkRepository
from evaluation.evaluation_helper import (
    format_results,
)


def evaluate_expression(logger_level=LoggerLevel.INFO):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'expression.fan')
    grammar, _ = parse_file(filename)

    benchmark = ExpressionBenchmarkRepository().build()
    expression = benchmark[0]

    # initial_inputs_failing, initial_inputs_passing = get_inputs(
    #     grammar,
    #     lambda x: expression.oracle(x)[0],
    # )
    # initial_inputs = initial_inputs_failing.union(initial_inputs_passing)
    initial_inputs = ["1 / (1 - 1)", "9 / 0" ,"1 + 3", "2 * 3", "4 - 2", "5 * (1 - 1)",]

    # initial_inputs = expression.get_initial_inputs()
    inps = []
    for inp in initial_inputs:
        oracle = expression.oracle(inp)[0]
        inps.append((inp, oracle))
        # print(inp, oracle)

    patterns = [
        Pattern(
            string_pattern="str(<NON_TERMINAL>) == <STRING>;",
        ),
        Pattern(
            string_pattern="exists <container> in <NON_TERMINAL>: exists <arith> in <container>.<rarithexp>: int(eval(str(<arith>))) == 0;",
        )
    ]

    initial_inputs = {
        FandangoInput.from_str(grammar, inp, oracle) for inp, oracle in inps
    }

    relevant_non_terminals = {
        NonTerminal("<arithexp>"),
        NonTerminal("<number>"),
        NonTerminal("<operator>"),
    }

    start_time_learning = time.time()
    learner = FandangoLearner(grammar, patterns=patterns, logger_level=logger_level)

    learned_constraints = learner.learn_constraints(
        initial_inputs, relevant_non_terminals=relevant_non_terminals
    )

    end_time_learning = time.time()

    # round time
    time_in_seconds = round(end_time_learning - start_time_learning, 4)
    return format_results(
        "Expression",
        grammar,
        lambda x: expression.oracle(x)[0],
        learned_constraints,
        time_in_seconds
    )


if __name__ == "__main__":
    random.seed(1)
    results = evaluate_expression()
    constraints = results["candidates"]
    for constraint in constraints:
        print(constraint)