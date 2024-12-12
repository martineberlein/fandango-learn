import pathlib
import time

from fandango.language.parse import parse_file
from fandangoLearner.learner import FandangoLearner, NonTerminal, FandangoInput


if __name__ == "__main__":
    grammar, _ = parse_file(pathlib.Path.cwd() / "calculator.fan")

    initial_inputs = {
        ("sqrt(-900)", True),
        ("sqrt(-10)", True),
        ("sqrt(0)", False),
        # ("sqrt(-1)", True),
        ("sin(-900)", False),
        ("sqrt(2)", False),
        ("cos(10)", False),
    }
    initial_inputs = {
        FandangoInput.from_str(grammar, inp, oracle) for inp, oracle in initial_inputs
    }

    relevant_non_terminals = {
        NonTerminal("<number>"),
        NonTerminal("<maybeminus>"),
        NonTerminal("<function>"),
    }

    start_time_learning = time.time()
    learner = FandangoLearner(grammar)

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
