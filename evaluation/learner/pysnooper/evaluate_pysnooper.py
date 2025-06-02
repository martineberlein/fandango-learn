import logging
import random
import os
import time

from fandango.language.symbol import NonTerminal

from fdlearn.data import FandangoInput, OracleResult
from fdlearn.logger import LoggerLevel
from fdlearn.learner import FandangoLearner
from fdlearn.interface.fandango import parse_file
from evaluation.evaluation_helper import format_results

logging.getLogger("tests4py").setLevel(logging.CRITICAL)

from debugging_benchmark.tests4py_benchmark.repository import (
    PysnooperBenchmarkRepository,
)


def evaluate_pysnooper2(logger_level=LoggerLevel.INFO, random_seed=1):
    random.seed(random_seed)
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "pysnooper2.fan")
    grammar, _ = parse_file(filename)

    program = PysnooperBenchmarkRepository().build()[0]

    def oracle(x):
        result = program.oracle(str(x))[0]
        if result.is_failing():
            return OracleResult.FAILING
        return OracleResult.PASSING

    initial_inputs = set()
    for inp in program.get_initial_inputs()[:12]:
        parsed = grammar.parse(inp)
        if parsed:
            initial_inputs.add(FandangoInput(parsed[0], oracle=oracle(parsed)))

    relevant_non_terminals = {
        NonTerminal("<op>"),
        NonTerminal("<custom_repr>"),
        NonTerminal("<predicate_list>"),
    }

    start_time_learning = time.time()
    learner = FandangoLearner(grammar, logger_level=logger_level)

    learned_constraints = learner.learn_constraints(
        initial_inputs,
        relevant_non_terminals=relevant_non_terminals,
        oracle=oracle,
    )

    end_time_learning = time.time()

    time_in_seconds = round(end_time_learning - start_time_learning, 4)
    return format_results(
        "Pysnooper2", grammar, oracle, learned_constraints, time_in_seconds, num_inputs=100
    )


def evaluate_pysnooper3(logger_level=LoggerLevel.INFO, random_seed=1):
    random.seed(random_seed)
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "pysnooper3.fan")
    grammar, _ = parse_file(filename)

    program = PysnooperBenchmarkRepository().build()[1]

    def oracle(x):
        result = program.oracle(str(x))[0]
        if result.is_failing():
            return OracleResult.FAILING
        return OracleResult.PASSING

    initial_inputs = set()
    for inp in program.get_initial_inputs()[:12]:
        parsed = grammar.parse(inp)
        if parsed:
            initial_inputs.add(FandangoInput(parsed[0], oracle=oracle(str(parsed))))

    relevant_non_terminals = {
        NonTerminal("<path>"),
        NonTerminal("<location>"),
        NonTerminal("<output>"),
    }

    start_time_learning = time.time()
    learner = FandangoLearner(grammar, logger_level=logger_level)

    learned_constraints = learner.learn_constraints(
        initial_inputs,
        relevant_non_terminals=relevant_non_terminals,
        oracle=oracle,
    )

    end_time_learning = time.time()

    time_in_seconds = round(end_time_learning - start_time_learning, 4)
    return format_results(
        "Pysnooper3", grammar, oracle, learned_constraints, time_in_seconds, num_inputs=100
    )


if __name__ == "__main__":
    results = evaluate_pysnooper2(random_seed=1, logger_level=LoggerLevel.INFO)
    print("Required Time: ", results["time_in_seconds"], " seconds")
    constraints = results["candidates"]
    for constraint in constraints:
        print(constraint)
    # results = evaluate_pysnooper3(random_seed=1)
    # print("Required Time: ", results["time_in_seconds"], " seconds")
    # constraints = results["candidates"]
    # for constraint in constraints:
    #     print(constraint)
