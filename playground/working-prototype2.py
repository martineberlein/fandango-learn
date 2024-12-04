from typing import List, Dict, Iterable, Set, Tuple
from itertools import product
from copy import deepcopy

from fandango.language.parse import parse, parse_file
from fandangoLearner.data.input import FandangoInput, OracleResult
from fandango.language.symbol import NonTerminal
from fandangoLearner.learning.candidate import FandangoConstraintCandidate
from fandango.constraints.base import ComparisonConstraint, Constraint
from fandango.language.search import RuleSearch

import math


def calculator_oracle(inp):
    try:
        eval(
            str(inp), {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan}
        )
    except ValueError:
        return OracleResult.FAILING
    return OracleResult.PASSING

def replace_non_terminals(patterns: Set[Constraint], non_terminal_values: Set[NonTerminal]) -> List[Tuple[Constraint, Set[NonTerminal]]]:
    replaced_patterns = []

    for pattern in patterns:
        #matches = list(pattern.searches.keys())
        matches = [key for key in list(pattern.searches.keys()) if pattern.searches[key].symbol == NonTerminal("<NON_TERMINAL>")]

        if matches:
            for replacements in product(list(non_terminal_values), repeat=len(matches)):
                new_searches = deepcopy(pattern.searches)
                for key, replacement in zip(matches, replacements):
                    if new_searches[key].symbol == NonTerminal("<NON_TERMINAL>"):
                        new_searches[key] = RuleSearch(replacement)
                if isinstance(pattern, ComparisonConstraint):
                    replaced_patterns.append(
                        (ComparisonConstraint(
                            operator=pattern.operator,
                            left=pattern.left,
                            right=pattern.right,
                            searches=new_searches,
                            local_variables=pattern.local_variables,
                            global_variables=pattern.global_variables
                        ), set(replacements)
                        )
                    )
        else:
            replaced_patterns.append((pattern, set()))
    return replaced_patterns


def replace_strings(
        patterns_with_non_terminals: (Set[Constraint],Set[NonTerminal]),
        string_values: Dict[NonTerminal, Iterable[str]]
) -> List[Tuple[Constraint, Set[NonTerminal]]]:

    replaced_patterns = []
    for pattern, non_terminals in patterns_with_non_terminals:
        matches = [key for key in list(pattern.searches.keys()) if
                              pattern.searches[key].symbol == NonTerminal("<STRING>")]
        if len(matches) > 0:
            if isinstance(pattern, ComparisonConstraint):
                for non_terminal in non_terminals:
                    for string_value in string_values.get(non_terminal, []):
                        new_right = pattern.right
                        for match in matches:
                            new_right = new_right.replace(match, f"'{string_value}'", 1)
                        new_searches = deepcopy(pattern.searches)
                        for key in matches:
                            del new_searches[key]
                        replaced_patterns.append(
                            (ComparisonConstraint(
                                operator=pattern.operator,
                                left=pattern.left,
                                right=new_right,
                                searches=new_searches,
                                local_variables=pattern.local_variables,
                                global_variables=pattern.global_variables
                            ),
                             non_terminals
                            )
                        )
        else:
            replaced_patterns.append((pattern, non_terminals))
    return replaced_patterns

def replace_integer(
        patterns_with_non_terminals: (Set[Constraint],Set[NonTerminal]),
        string_values: Dict[NonTerminal, Iterable[str]]
) -> List[Tuple[Constraint, Set[NonTerminal]]]:

    replaced_patterns = []
    for pattern, non_terminals in patterns_with_non_terminals:
        matches = [key for key in list(pattern.searches.keys()) if
                              pattern.searches[key].symbol == NonTerminal("<INTEGER>")]
        if len(matches) > 0:
            if isinstance(pattern, ComparisonConstraint):
                for non_terminal in non_terminals:
                    for string_value in string_values.get(non_terminal, []):
                        new_right = pattern.right
                        for match in matches:
                            new_right = new_right.replace(match, f'{string_value}', 1)
                        new_searches = deepcopy(pattern.searches)
                        for key in matches:
                            del new_searches[key]
                        replaced_patterns.append(
                            (ComparisonConstraint(
                                operator=pattern.operator,
                                left=pattern.left,
                                right=new_right,
                                searches=new_searches,
                                local_variables=pattern.local_variables,
                                global_variables=pattern.global_variables
                            ),
                             non_terminals
                            )
                        )
        else:
            replaced_patterns.append((pattern, non_terminals))
    return replaced_patterns


def is_number(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False

def extract_non_terminal_values(relevant_non_terminals: Set[NonTerminal], initial_inputs: Set[FandangoInput]) -> Dict[
    str, Dict[NonTerminal, List[str]]]:
    string_values = {}
    int_values = {}
    for non_terminal in relevant_non_terminals:
        for inp in initial_inputs:
            found_trees = inp.tree.find_all_trees(NonTerminal(non_terminal.symbol))
            for tree in found_trees:
                value = str(tree)
                if is_number(value):
                    int_values.setdefault(non_terminal, []).append(value)
                else:
                    string_values.setdefault(non_terminal, []).append(value)
    return {
        "string_values": {k: list(set(v)) for k, v in string_values.items()},
        "int_values": {k: list(set(v)) for k, v in int_values.items()},
    }


if __name__ == "__main__":
    import time

    grammar, _ = parse_file('calculator.fan')
    test_inputs = [
        ("sqrt(-900)", OracleResult.FAILING),
        ("sqrt(-1)", OracleResult.FAILING),
        ("sin(-900)", OracleResult.PASSING),
        ("sqrt(2)", OracleResult.PASSING),
        ("cos(10)", OracleResult.PASSING),
    ]

    initial_inputs = {FandangoInput.from_str(grammar, inp, result) for inp, result in test_inputs}

    patterns = [
        "int(<NON_TERMINAL>) <= <INTEGER>;",
        "int(<NON_TERMINAL>) == <INTEGER>;",
        "str(<NON_TERMINAL>) == <STRING>;",
        "int(<NON_TERMINAL>) == len(str(<NON_TERMINAL>));",
        "int(<NON_TERMINAL>) == int(<NON_TERMINAL>) * <INTEGER> * int(<NON_TERMINAL>) * <INTEGER>;",
    ]

    start_time = time.time()
    print("Start parsing patterns:")
    initialized_patterns = set()
    for pattern in patterns:
        initialized_patterns.add(parse(pattern)[1][0])

    parse_time = time.time()
    print("Time taken to parse patterns:", parse_time - start_time)
    print("Start replacing non-terminals:")

    print("Start Restruct:")
    non_terminal_values = {NonTerminal("<number>"), NonTerminal("<maybeminus>"), NonTerminal("<function>")}
    extracted_values = extract_non_terminal_values(non_terminal_values, initial_inputs)
    print(extracted_values)

    cand = replace_non_terminals(initialized_patterns, non_terminal_values)
    cand = replace_strings(cand, extracted_values["string_values"])
    cand = replace_integer(cand, extracted_values["int_values"])

    instantition_time = time.time() - parse_time
    print("Time taken to replace non-terminals:", instantition_time)

    candidates = []
    for can in cand:
        candidate = FandangoConstraintCandidate(can[0])
        try:
            candidate.evaluate(initial_inputs)
            if candidate.recall() >= 0.8:
                candidates.append(candidate)
        except:
            continue

    for candidate in candidates:
        candidate.reset()

    print("Filtered Learned Atomic Constraints: ")
    for candidate in candidates:
        candidate.evaluate(initial_inputs)
        print("Constraint:", candidate.constraint, "Recall:", candidate.recall(), "Precision:", candidate.precision())
    print("\n")

    print("Time taken to learn constraints:", time.time() - start_time)

    for _ in range(2000):
        inp = grammar.fuzz()
        test_inputs.append((str(inp), calculator_oracle(inp)))

    evaluation_inputs = {FandangoInput.from_str(grammar, inp, result) for inp, result in test_inputs}

    start_time = time.time()
    print("Evaluate Constraints with: ", len(evaluation_inputs), "inputs")
    for candidate in candidates:
        candidate.evaluate(evaluation_inputs)
        print("Constraint:", candidate.constraint, "Recall:", candidate.recall(), "Precision:", candidate.precision())
    print("\n")

    print("Time taken to evaluate constraints:", time.time() - start_time)



