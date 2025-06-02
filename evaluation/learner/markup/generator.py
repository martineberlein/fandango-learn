import os

from debugging_benchmark.markup.markup import MarkupBenchmarkRepository

from fandango.evolution.algorithm import Fandango

from fdlearn.interface.fandango import parse


import random
import os

from typing import Collection

from fdlearn.interface.fandango import parse
from fdlearn.data.input import FandangoInput, OracleResult
from fdlearn.learner import FandangoLearner
from fdlearn.logger import LoggerLevel
from fdlearn.resources.patterns import Pattern
from fdlearn.refinement.mutation import MutationFuzzer
import hashlib


def stable_hash(value: str, length: int = 8) -> str:
    return hashlib.sha1(value.encode()).hexdigest()[:length]



def generate_more_failing(bug_oracle, grammar_, samples_: Collection[FandangoInput]) -> tuple[list[FandangoInput], list[FandangoInput]]:
    seeds = [inp for inp in samples_ if inp.oracle.is_failing()]

    mutation_fuzzer = MutationFuzzer(grammar_, seed_inputs=seeds, oracle=bug_oracle)

    positive_inputs = []
    negative_inputs = []

    while len(positive_inputs) < 100:
        try:
            inp = next(mutation_fuzzer.run(yield_negatives=True))
            if inp.oracle == OracleResult.FAILING:
                positive_inputs.append(inp)
            else:
                negative_inputs.append(inp)
            write_to_file([inp], "Markup2")
        except StopIteration:
            break

    return positive_inputs, negative_inputs


def write_to_file(inputs: list[FandangoInput], subject_name: str):
    os.makedirs(f"{subject_name}/positive_inputs", exist_ok=True)
    os.makedirs(f"{subject_name}/negative_inputs", exist_ok=True)

    for inp in inputs:
        try:
            filename = f"{subject_name}_{stable_hash(str(inp))}.txt"
            base_dir = subject_name
            directory = "positive_inputs" if inp.oracle.is_failing() else "negative_inputs"
            filepath = os.path.join(base_dir, directory, filename)

            with open(filepath, "w") as f:
                f.write(str(inp))

        except Exception as e:
            print(f"Error writing input: {inp}\nException: {e}")


if __name__ == "__main__":
    random.seed(2)
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "markup_gen.fan")
    grammar, constraints = parse(filename)

    programs = MarkupBenchmarkRepository().build()
    program = programs[1]  # Markup.1

    def oracle(x):
        result_ = program.oracle(x)
        result = result_[0] if isinstance(result_, (list, tuple)) else result_
        if result.is_failing():
            return OracleResult.FAILING
        if str(result) == "UNDEFINED":
            return OracleResult.UNDEFINED
        return OracleResult.PASSING

    initial = [(inp, oracle(inp).is_failing()) for inp in program.get_initial_inputs()]

    initial_inputs = {
        FandangoInput.from_str(grammar, inp, oracle) for inp, oracle in initial
    }
    for inp in initial_inputs:
        print(inp, inp.oracle)

    pos_inputs, neg_inputs = generate_more_failing(oracle, grammar, initial_inputs)
    write_to_file(pos_inputs + neg_inputs, "Markup2")
    for inp in pos_inputs:
        print(inp, inp.oracle)

    print(f"Positive inputs: {len(pos_inputs)}")
    print(f"Negative inputs: {len(neg_inputs)}")
    initial_inputs.update(pos_inputs)
    initial_inputs.update(neg_inputs)
