import time

from fandango.language.parse import parse_file
from fandango.language.symbol import NonTerminal
from fandangoLearner.learner import FandangoLearner
from fandangoLearner.input import FandangoInput

from evaluation_helper import evaluate_candidates, get_inputs, print_constraints
from resources.heartbeat import initial_inputs, oracle_simple as oracle

if __name__ == "__main__":
    grammar, _ = parse_file("heartbleed.fan")

    initial_inputs = {
        FandangoInput.from_str(grammar, inp, oracle(inp))
        for inp in initial_inputs
    }

    relevant_non_terminals = {
        NonTerminal("<payload>"),
        NonTerminal("<payloadlength>"),
    }

    start_time_learning = time.time()
    learner = FandangoLearner(grammar)

    candidates = learner.learn_constraints(initial_inputs, relevant_non_terminals)

    end_time_learning = time.time()

    print(
        f"Time taken to learn constraints: {end_time_learning - start_time_learning:.4f} seconds",
        end="\n\n",
    )

    print_constraints(candidates, initial_inputs)

    print()
    evaluate_candidates(candidates, grammar, oracle)
