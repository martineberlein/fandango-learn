import math
import random
import time

from islearn.learner import InvariantLearner
from isla.language import DerivationTree, EarleyParser
from islearn.language import ISLaUnparser
from debugging_benchmark.calculator.calculator import calculator_grammar


def calculator_oracle(inp):
    try:
        eval(
            str(inp),
            {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan},
        )
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    random.seed(1)
    initial_inputs_strings = {
        ("sqrt(-900)", True),
        ("sqrt(-10)", True),
        # ("sqrt(0)", False),
        ("sqrt(1)", False),
        ("sin(-900)", False),
        ("sqrt(2)", False),
        ("cos(10)", False),
    }
    parser = EarleyParser(calculator_grammar)
    positive = {
        DerivationTree.from_parse_tree(list(parser.parse(inp))[0])
        for inp, res in initial_inputs_strings
        if res is True
    }
    # print([str(inp) for inp in positive])
    negative = {
        DerivationTree.from_parse_tree(list(parser.parse(inp))[0])
        for inp, res in initial_inputs_strings
        if res is False
    }
    # print([str(inp) for inp in negative])

    start_time = time.time()

    learner = InvariantLearner(
        calculator_grammar,
        positive_examples=positive,
        negative_examples=negative,
        do_generate_more_inputs=False,
        generate_new_learning_samples=False,
        prop=calculator_oracle,
        exclude_nonterminals={
            "<arith_expr>",
            "<maybe_frac>",
            "<one_nine>",
            "<digit>",
            "<maybe_digits>",
            "<maybe_minus>",
            "<digits>",
        },
    )
    candidates = learner.learn_invariants()

    end_time = time.time() - start_time
    print(f"Time: {end_time:.4f} seconds")

    print(
        "\n".join(
            map(
                lambda p: f"{p[1]}: " + ISLaUnparser(p[0]).unparse(),
                {f: p for f, p in candidates.items() if p[0] >= 1.0}.items(),
            )
        )
    )
