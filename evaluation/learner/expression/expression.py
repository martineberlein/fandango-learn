import os
import time
import random

from fdlearn.interface.fandango import parse_file
from fdlearn.learner import FandangoLearner, NonTerminal, FandangoInput
from fdlearn.logger import LoggerLevel
from fdlearn.resources.patterns import Pattern
from fdlearn.data.oracle import OracleResult

from debugging_benchmark.expression.expression import ExpressionBenchmarkRepository
from evaluation.evaluation_helper import (
    format_results,
)


def evaluate_expression(logger_level=LoggerLevel.INFO, random_seed=1):
    random.seed(random_seed)
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "expression.fan")
    grammar, _ = parse_file(filename)

    benchmark = ExpressionBenchmarkRepository().build()
    expression = benchmark[0]

    def oracle(x):
        result_ = expression.oracle(x)
        result = result_[0] if isinstance(result_, (list, tuple)) else result_
        if result.is_failing():
            return OracleResult.FAILING
        if str(result) == "UNDEFINED":
            return OracleResult.UNDEFINED
        return OracleResult.PASSING

    initial_inputs = [
        "1 / (1 - 1)",
        "9 / 0",
        "1 + 3",
        "2 * 3",
        "4 - 2",
        "5 * (1 - 1)",
    ]

    initial_inputs = expression.get_initial_inputs()
    inps = []
    for inp in initial_inputs:
        inps.append((inp, oracle(inp)))
        print(inp, oracle(inp))

    patterns = [
        Pattern(
            string_pattern="exists <elem> in <NON_TERMINAL>: str(<elem>) == <STRING>;",
        ),
        # Pattern(
        #     string_pattern="exists <container> in <NON_TERMINAL>: exists <arith> in <container>.<rarithexp>: int(eval(str(<arith>))) == 0;",
        # ),
    ]

    initial_inputs = {
        FandangoInput.from_str(grammar, inp, oracle) for inp, oracle in inps
    }

    relevant_non_terminals = {
        NonTerminal("<arithexp>"),
        NonTerminal("<number>"),
        NonTerminal("<operator>"),
    }

    relevant_non_terminals = None
    start_time_learning = time.time()
    learner = FandangoLearner(grammar, patterns=patterns, logger_level=logger_level)

    learned_constraints = learner.learn_constraints(
        initial_inputs, relevant_non_terminals=relevant_non_terminals
    )
    for explanation in learned_constraints:
        print(explanation, explanation.precision(), explanation.recall())

    end_time_learning = time.time()

    # round time
    time_in_seconds = round(end_time_learning - start_time_learning, 4)
    return format_results(
        "Expression",
        grammar,
        oracle,
        learned_constraints,
        time_in_seconds,
    )


if __name__ == "__main__":
    random.seed(1)
    results = evaluate_expression()
    constraints = results["candidates"]
    for constraint in constraints:
        print(constraint)
