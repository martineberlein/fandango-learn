import pathlib
import time

from fandango.language.parse import parse_file

from evaluation.heartbleed.heartbeat import initial_inputs
from fandangoLearner.learner import FandangoLearner, NonTerminal, FandangoInput
from fandangoLearner.resources.patterns import Pattern

from debugging_benchmark.expression.expression import ExpressionBenchmarkRepository
from evaluation.evaluation_helper import (
    evaluate_candidates,
    get_inputs,
    print_constraints,
)


if __name__ == "__main__":
    grammar, _ = parse_file(pathlib.Path.cwd() / "expression.fan")

    benchmark = ExpressionBenchmarkRepository().build()
    expression = benchmark[0]

    # initial_inputs_failing, initial_inputs_passing = get_inputs(
    #     grammar,
    #     lambda x: expression.oracle(x)[0],
    # )
    # initial_inputs = initial_inputs_failing.union(initial_inputs_passing)
    #initial_inputs = ["1 / (1 - 1)", "9 / 0" ,"1 + 3", "2 * 3", "4 - 2",]

    initial_inputs = expression.get_initial_inputs()
    inps = []
    for inp in initial_inputs:
        oracle = expression.oracle(inp)[0]
        inps.append((inp, oracle))
        print(inp, oracle)


    patterns = [
        # Pattern(
        #     string_pattern="exists <cont> in <NON_TERMINAL>: str(<cont>) == <STRING>;",
        # ),
        Pattern(
            string_pattern="exists <container> in <NON_TERMINAL>: exists <arith> in <container>.<larithexp>: int(eval(str(<arith>))) == 0;",
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
    learner = FandangoLearner(grammar, patterns=patterns)

    learned_constraints = learner.learn_constraints(
        initial_inputs, relevant_non_terminals=relevant_non_terminals
    )

    end_time_learning = time.time()

    for constraint in learner.get_best_candidates():
        print(constraint)

    print(
        f"Time taken to learn constraints: {end_time_learning - start_time_learning:.4f} seconds",
        end="\n\n",
    )
