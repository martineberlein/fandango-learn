import random
import sys
import os
import xml.etree.ElementTree as ET
from typing import Callable, Union
from pathlib import Path

from fandango.evolution.algorithm import Fandango
from fandango.language.parse import parse, Grammar

from fdlearn.data import OracleResult
from fdlearn.learner import FandangoLearner, FandangoInput, NonTerminal


def oracle(inp: str | FandangoInput) -> OracleResult:
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


def get_xml_subject() -> tuple[
    Grammar,
    list[FandangoInput],
    Callable[[str | FandangoInput], OracleResult],
    dict,
]:
    base_dir = Path(__file__).parent
    with open(base_dir / "xml.fan", "r") as file:
        grammar, _ = parse(file, use_cache=False, use_stdlib=False)

    initial_inputs = []
    additional_param = {"name": "XML"}

    return grammar, initial_inputs, oracle, additional_param


# def evaluate_csv(
#     seconds=60,
# ) -> tuple[str, int, int, float, tuple[float, int, int], float, float]:
#     with open("csv.fan", "r") as file:
#         grammar, consts = parse(file, use_cache=False, use_stdlib=False)
#
#     print(consts[0].statement.statement)
#     right = consts[0].statement.statement.left
#     print(type(consts[0].statement.statement.searches[right]))
#     print(consts[0].statement.statement.searches[right].get_access_points())
#     # exit(0)
#     valid, invalid = set(), set()
#     while len(valid) < 100 and len(invalid) < 100:
#         tree = grammar.fuzz()
#         inp = tree.to_string()
#         if is_syntactically_valid_csv(inp):
#             valid.add(inp)
#         else:
#             invalid.add(inp)
#
#     print(f"Found {len(valid)} vaild and {len(valid)} invalid CSV files.")
#     print("--- Learning Invariant ---", end="\n\n")
#
#     positive_inputs = {FandangoInput.from_str(grammar, inp, True) for inp in valid}
#     negative_inputs = {FandangoInput.from_str(grammar, inp, False) for inp in invalid}
#     initial_inputs = positive_inputs.union(negative_inputs)
#
#     pattern = [
#         # Pattern(
#         #     string_pattern="""where forall <r1> in <NON_TERMINAL>: forall <r2> in <NON_TERMINAL>: len(*<r1>..<raw_field>) == len(*<r2>..<raw_field>)""",
#         # ),
#         # Pattern(
#         #     string_pattern="""where forall <r1> in <NON_TERMINAL>: forall <r2> in <NON_TERMINAL>: len(*<r1>..<raw_field>) == len(*<r2>..<raw_field>)""",
#         # ),
#         Pattern(
#             string_pattern="""where forall <r1> in <NON_TERMINAL>: forall <r2> in <NON_TERMINAL>: len(*<ATTRIBUTE>) == len(*<ATTRIBUTE>)""",
#         )
#     ]
#
#     fdlearn = FandangoLearner(
#         grammar=grammar,
#         # patterns=pattern,
#     )
#     invariants = fdlearn.learn_constraints(test_inputs=initial_inputs)
#
#     for invariant in invariants:
#         print("Learned Invariant: ", invariant)
#
#     best_invariant = invariants[0] if invariants else None
#
#     end_time = time.time() + seconds
#     solutions = []
#     fan_gen = Fandango(grammar=grammar, constraints=[best_invariant.constraint]).generate()
#     for inp in fan_gen:
#         solutions.append(inp)
#         if time.time() >= end_time:
#             break
#
#
#     coverage = grammar.compute_grammar_coverage(solutions, 4)
#
#     valid = []
#     for solution in solutions:
#         if is_syntactically_valid_csv(str(solution)):
#             valid.append(solution)
#
#     set_mean_length = sum(len(str(x)) for x in valid) / len(valid)
#     set_medium_length = sorted(len(str(x)) for x in valid)[len(valid) // 2]
#     valid_percentage = len(valid) / len(solutions) * 100
#     return (
#         "CSV",
#         len(solutions),
#         len(valid),
#         valid_percentage,
#         coverage,
#         set_mean_length,
#         set_medium_length,
#     )
#
#
# if __name__ == "__main__":
#     # result = evaluate_csv_grammar_fuzzer(seconds=10)
#     # print(
#     #     f"Type: {result[0]}, "
#     #     f"Solutions: {result[1]}, "
#     #     f"Valid: {result[2]}, "
#     #     f"Valid Percentage: {result[3]:.2f}%, "
#     #     f"Coverage: {result[4]}, "
#     #     f"Mean Length: {result[5]:.2f}, "
#     #     f"Medium Length: {result[6]:.2f}"
#     # )
#
#     result = evaluate_csv(seconds=10)
#     print(
#         f"Type: {result[0]}, "
#         f"Solutions: {result[1]}, "
#         f"Valid: {result[2]}, "
#         f"Valid Percentage: {result[3]:.2f}%, "
#         f"Coverage: {result[4]}, "
#         f"Mean Length: {result[5]:.2f}, "
#         f"Medium Length: {result[6]:.2f}"
#     )
