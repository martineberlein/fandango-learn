from fandango.language.parse import parse_file
from fandango.evolution.algorithm import Fandango

from evaluation.heartbleed.heartbeat import initial_inputs
from fandangoLearner.data.input import FandangoInput
from fandangoLearner.learner import FandangoLearner, NonTerminal
from fandangoLearner.resources.patterns import Pattern

if __name__ == "__main__":
    grammar, constraints = parse_file("calculator.fan")

    initial_inputs = [
        ("sqrt(4)", True),
        ("sqrt(0)", False),
        #("cos(4)", False),
    ]

    initial_inputs = {FandangoInput.from_str(grammar, inp, oracle) for inp, oracle in initial_inputs}

    patterns = [
        Pattern(
            string_pattern="import math\n"
                           "eval(str(<NON_TERMINAL>),  {'sqrt': math.sqrt, 'cos': math.cos}) == <INTEGER>;",
            use_cache=False
        )
    ]

    relevant_non_terminals = {
        NonTerminal("<arithexp>"),
        NonTerminal("<number>"),
        NonTerminal("<operator>"),
    }

    learner = FandangoLearner(grammar, patterns=patterns)

    learned_constraints = learner.learn_constraints(
        initial_inputs, relevant_non_terminals=relevant_non_terminals
    )

    for constraint in learner.get_best_candidates():
        print(constraint)