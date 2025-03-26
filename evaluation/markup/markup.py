import time
import os
import random

from fdlearn.data import OracleResult
from fdlearn.interface.fandango import parse_file
from fandango.language.symbol import NonTerminal
from fdlearn.learner import FandangoLearner
from fdlearn.logger import LoggerLevel

#from debugging_benchmark.tests4py_benchmark.repository import MarkUpBenchmarkRepository
from debugging_benchmark.markup.markup import MarkupBenchmarkRepository
from debugging_benchmark.markup.markup import grammar_markup
from evaluation.evaluation_helper import format_results


def evaluate_markup(logger_level=LoggerLevel.INFO, random_seed=1):
    random.seed(random_seed)
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "markup.fan")
    print("parsing file: ", filename)
    grammar, _ = parse_file(filename)

    print(grammar)
    print(grammar.parse("This is a strong <s>Sentence</s>!"))

    programs = MarkupBenchmarkRepository().build()
    program = programs[0]  # Markup.1

    for inp in program.get_initial_inputs():
        print(inp)
        print(
            grammar.parse(inp)
        )

    def oracle(x):
        result = program.oracle(x)[0]
        if result.is_failing():
            return OracleResult.FAILING
        return OracleResult.PASSING

    initial_inputs = set(program.get_initial_inputs())

    from fdlearn.resources.patterns import Pattern
    patterns = [
        Pattern(
            string_pattern="exists <elem> in <NON_TERMINAL>: is_inside(<elem>, <start>);",
        ),
        Pattern(
            string_pattern="exists <context> in <NON_TERMINAL>: exists <elem> in <context>: str(<elem>) == '\"';",
        ),
        Pattern(
            string_pattern="exists <elem> in <NON_TERMINAL>: str(<elem>) == <STRING>;",
        )
    ]

    start_time_learning = time.time()
    learner = FandangoLearner(grammar, patterns=patterns, logger_level=logger_level)

    candidates = learner.learn_constraints(
        initial_inputs,
        oracle=oracle,
    )

    for explanation in candidates:
        print(explanation)

    end_time_learning = time.time()

    # round time
    time_in_seconds = round(end_time_learning - start_time_learning, 4)
    return format_results(
        "Markup1", grammar, oracle, candidates, time_in_seconds
    )


if __name__ == "__main__":
    random.seed(1)
    results = evaluate_markup(LoggerLevel.INFO)
    print("Required Time: ", results["time_in_seconds"], " seconds")
    constraints = results["candidates"]
    for constraint in constraints:
        print(constraint)
