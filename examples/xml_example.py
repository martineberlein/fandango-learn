import random
import sys
import os
import xml.etree.ElementTree as ET
from pathlib import Path

from fandango.evolution.algorithm import Fandango
from fandango.language.parse import parse

from fdlearn.data import OracleResult
from fdlearn.learner import FandangoLearner, FandangoInput, NonTerminal
from fdlearn.interface.fandango import parse_contents


def oracle(inp: str) -> OracleResult:
    """
    Oracle function to validate IBANs.
    """
    try:
        ET.fromstring(str(inp))
    except ET.ParseError:
        return OracleResult.PASSING
    except Exception:
        return OracleResult.UNDEFINED
    return OracleResult.FAILING


if __name__ == "__main__":
    random.seed(1)  # For reproducibility
    with open("xml.fan", "r") as f:
        grammar, _ = parse(f, use_cache=False, use_stdlib=False)

    positive, negative = set(), set()
    while len(positive) < 10:
        tree = grammar.fuzz()
        inp = tree.to_string()
        if oracle(inp).is_failing():
            positive.add(inp)
        else:
            negative.add(inp)

    print(f"Found {len(positive)} valid and {len(negative)} invalid inputs.")

    print("--- Learning Invariant ---", end="\n\n")

    positive_inputs = [
        FandangoInput.from_str(grammar, inp, True) for inp in list(positive)[:100]
    ]
    negative_inputs = [
        FandangoInput.from_str(grammar, inp, False) for inp in list(negative)[:100]
    ]
    initial_inputs = positive_inputs + negative_inputs

    relevant_non_terminals = {
        NonTerminal("<xml_tree>"),
        NonTerminal("<xml_open_tag>"),
        NonTerminal("<xml_close_tag>"),
        NonTerminal("<id>"),
    }

    learner = FandangoLearner(grammar)
    learned_constraints = learner.learn_constraints(
        initial_inputs, relevant_non_terminals=relevant_non_terminals
    )

    for invariant in learner.get_best_candidates():
        print("Learned Invariant: ", invariant)

    invariant = learner.get_best_candidates()[0].constraint

    print("--- Generating IBANs ---")
    print("Using Invariant ", invariant, " to generate valid XML instances", end="\n\n")

    solutions = set()

    fandango = Fandango(grammar, [invariant])
    fandango_generator = fandango.generate()

    for inp in fandango_generator:
        solutions.add(inp)
        if len(solutions) >= 10:
            break

    tp = [tree for tree in solutions if oracle(str(tree)).is_failing()]
    fp = [tree for tree in solutions if not oracle(str(tree)).is_failing()]

    print("--- Invariant Evaluation ---")
    print(f"Generated {len(tp)} valid XML and {len(fp)} invalid XML instances.")

    # for tree in fp:
    #     print("Invalid: ", tree.to_string())
    #
    # for tree in tp:
    #     print("Valid: ", tree.to_string())
