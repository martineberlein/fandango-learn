import random
from typing import Collection
from pathlib import Path

from dbgbench.framework.oraclesresult import OracleResult
from dbgbench.resources import get_grep_grammar_path, get_grep_samples
from dbgbench.framework.util import escape_non_ascii_utf8
from dbgbench.framework.data import load_from_files
from dbgbench.subjects import Grep3c3bdace

from fdlearn.interface.fandango import parse
from fdlearn.data.input import FandangoInput
from fdlearn.learner import FandangoLearner
from fdlearn.logger import LoggerLevel
from fdlearn.resources.patterns import Pattern
from fdlearn.learning.metric import RecallPriorityFitness


if __name__ == "__main__":
    random.seed(1)

    bug_type = Grep3c3bdace

    grep_grammar = get_grep_grammar_path()
    grammar, _ = parse(grep_grammar)

    #samples = get_grep_samples()
    with bug_type() as bug:
        samples_paths = bug.sample_files(get_all=True)
        samples = [file.read_text() for file in samples_paths]
        result = bug.execute_samples(samples)

    test_inputs = []
    for inp, oracle in result:
        oracle_bool = True if oracle == OracleResult.FAILING else False
        test_inputs.append((escape_non_ascii_utf8(inp), oracle_bool))

    initial_inputs = {
        FandangoInput.from_str(grammar, inp, oracle) for inp, oracle in test_inputs
    }
    for inp in initial_inputs:
        print(inp, inp.oracle)

    patterns = [
        Pattern(
            string_pattern="exists <elem> in <NON_TERMINAL>: is_inside(<elem>, <start>);",
        ),
        Pattern(
            string_pattern="str(<NON_TERMINAL>) == <STRING>;",
        )
    ]

    # initial_inputs = list(positive_inputs) + list(negative_inputs)

    learner = FandangoLearner(grammar, patterns=patterns, logger_level=LoggerLevel.INFO) # +, max_conjunction_size=3)

    learned_constraints = learner.learn_constraints(
        initial_inputs
    )

    evaluation_data = []
    positive_data = load_from_files(str(Path.home()) + f"/.dbgbench/{bug_type.__name__}/positive_inputs")
    positive_inputs = {FandangoInput.from_str(grammar, inp, True) for inp in positive_data}

    negative_data = load_from_files(str(Path.home()) + f"/.dbgbench/{bug_type.__name__}/negative_inputs")[:100]
    negative_inputs = {FandangoInput.from_str(grammar, inp, False) for inp in negative_data}


    for constraint in learned_constraints:
        constraint.evaluate(positive_inputs)
        constraint.evaluate(negative_inputs)

    sorting_strategy = RecallPriorityFitness()
    learned_constraints = sorted(learned_constraints, key=lambda exp: sorting_strategy.evaluate(exp), reverse=True)
    for constraint in learned_constraints:
        print(constraint)
