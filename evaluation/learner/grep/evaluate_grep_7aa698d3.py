import random
from typing import Collection

from dbgbench.framework.oraclesresult import OracleResult
from dbgbench.resources import get_grep_grammar_path, get_grep_samples
from dbgbench.framework.util import escape_non_ascii_utf8
from dbgbench.subjects import Grep7aa698d3

from fdlearn.interface.fandango import parse
from fdlearn.data.input import FandangoInput
from fdlearn.learner import FandangoLearner
from fdlearn.logger import LoggerLevel
from fdlearn.resources.patterns import Pattern
from fdlearn.refinement.mutation import MutationFuzzer


def generate_more_failing(bug_type_, grammar_, samples_: Collection[FandangoInput]) -> tuple[list[FandangoInput], list[FandangoInput]]:

    def bug_oracle(inp):
        with bug_type_() as bug:
            res = bug.execute_sample(str(inp))
        return res

    seeds = [inp for inp in samples_ if inp.oracle == OracleResult.FAILING]

    mutation_fuzzer = MutationFuzzer(grammar_, seed_inputs=seeds, oracle=bug_oracle)

    positive_inputs = []
    negative_inputs = []

    while len(positive_inputs) < 5:
        try:
            inp = next(mutation_fuzzer.run(yield_negatives=True))
            if inp.oracle == OracleResult.FAILING:
                positive_inputs.append(inp)
            else:
                negative_inputs.append(inp)
        except StopIteration:
            break

    return positive_inputs, negative_inputs

if __name__ == "__main__":
    random.seed(1)
    bug_type = Grep7aa698d3

    grep_grammar = get_grep_grammar_path()
    grammar, _ = parse(grep_grammar)

    with bug_type() as bug:
        samples = bug.sample_inputs()
        result = bug.execute_samples(samples)

    test_inputs = []
    for inp, oracle in result:
        oracle_bool = True if oracle == OracleResult.FAILING else False
        test_inputs.append((escape_non_ascii_utf8(inp), oracle_bool))

    initial_inputs = {
        FandangoInput.from_str(grammar, inp, oracle) for inp, oracle in test_inputs
    }

    pos_inputs, neg_inputs = generate_more_failing(bug_type, grammar, initial_inputs)
    print(f"Positive inputs: {len(pos_inputs)}")
    print(f"Negative inputs: {len(neg_inputs)}")
    initial_inputs.update(pos_inputs)
    initial_inputs.update(neg_inputs)

    patterns = [
        Pattern(
            string_pattern="exists <elem> in <NON_TERMINAL>: is_inside(<elem>, <start>);",
        ),
        Pattern(
            string_pattern="str(<NON_TERMINAL>) == <STRING>;",
        )
    ]

    learner = FandangoLearner(grammar, patterns=patterns, logger_level=LoggerLevel.INFO)

    learned_constraints = learner.learn_constraints(
        initial_inputs
    )

    for constraint in learned_constraints:
        print(constraint)