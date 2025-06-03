import random
from fandango.evolution.algorithm import Fandango

from fdlearn.data import OracleResult
from fdlearn.learner import FandangoLearner, FandangoInput
from fdlearn.interface.fandango import parse_contents
from fdlearn.resources import Pattern

grammar = """
<start> ::= <arithexp>;
<arithexp> ::= <term> | <number> | "(" <arithexp> ")";
<term> ::= <arithexp><operator><rarithexp>;
<rarithexp> ::= <arithexp>;
<operator> ::= " + " | " - " | " * " | " / ";
<number> ::= <maybeminus><onenine><maybedigits> | "0";
<maybeminus> ::= "~ " | "";
<onenine> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
<maybedigits> ::= <digit>*;
<digit>::=  "0" | <onenine>;
"""


def oracle(inp: str) -> OracleResult:
    """
    Oracle function to validate IBANs.
    """
    try:
        eval(inp)
    except ZeroDivisionError:
        return OracleResult.FAILING
    except Exception:
        return OracleResult.UNDEFINED
    return OracleResult.PASSING


if __name__ == "__main__":
    random.seed(1)  # For reproducibility
    grammar, _ = parse_contents(grammar)

    positive, negative = set(), set()
    while len(positive) < 10 :
        tree = grammar.fuzz()
        inp = tree.to_string()
        if oracle(inp).is_failing():
            positive.add(inp)
            print(inp)
        else:
            negative.add(inp)

    print(f"Found {len(positive)} valid and {len(negative)} invalid inputs.")

    print("--- Learning Invariant ---", end="\n\n")

    positive_inputs = {FandangoInput.from_str(grammar, inp, True) for inp in positive}
    negative_inputs = {FandangoInput.from_str(grammar, inp, False) for inp in negative}
    initial_inputs = positive_inputs.union(negative_inputs)

    learner = FandangoLearner(grammar)
    learned_constraints = learner.learn_constraints(
        initial_inputs,
    )

    for invariant in learner.get_best_candidates():
        print("Learned Invariant: ", invariant)

    invariant = learner.get_best_candidates()[0].constraint

    print("--- Generating IBANs ---")
    print("Using Invariant ", invariant, " to generate valid IBANs", end="\n\n")

    solutions = set()

    while len(solutions) < 10:
        fandango = Fandango(grammar, [invariant])
        population = fandango.evolve()
        for tree in population:
            solutions.add(tree)

    tp = [True for tree in solutions if oracle(str(tree)).is_failing()]
    fp = [True for tree in solutions if not oracle(str(tree)).is_failing()]

    print("--- Invariant Evaluation ---")
    print(f"Generated {len(tp)} valid IBANs and {len(fp)} invalid IBANs.")
