from typing import List, Dict, Iterable
import re
from itertools import product
from enum import Enum
import math

from fandango.language.parse import parse, parse_file
from fandangoLearner.input import FandangoInput, OracleResult
from fandango.language.symbol import NonTerminal
from fandangoLearner.candidate import FandangoConstraintCandidate


def calculator_oracle(inp):
    try:
        eval(
            str(inp), {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan}
        )
    except ValueError:
        return OracleResult.FAILING
    return OracleResult.PASSING


class PlaceholderVariable(Enum):
    NON_TERMINAL_PLACEHOLDER = "NON_TERMINAL"
    STRING_PLACEHOLDER = "STRING"
    INTEGER_PLACEHOLDER = "INTEGER"

    def __str__(self):
        return self.value


def replace_non_terminals(patterns: List[str], non_terminal_values: Iterable[str]) -> List[Dict[str, List[str]]]:
    non_terminal_placeholder = re.compile(r"<\?NON_TERMINAL>")
    replaced_patterns = []
    for pattern in patterns:
        matches = non_terminal_placeholder.findall(pattern)
        if matches:
            for replacements in product(non_terminal_values, repeat=len(matches)):
                updated_pattern = pattern
                used_non_terminals = []
                for replacement in replacements:
                    updated_pattern = updated_pattern.replace("<?NON_TERMINAL>", replacement, 1)
                    used_non_terminals.append(replacement)
                replaced_patterns.append({"pattern": updated_pattern, "non_terminals": used_non_terminals})
        else:
            replaced_patterns.append({"pattern": pattern, "non_terminals": []})
    return replaced_patterns


def replace_strings(patterns_with_non_terminals: List[Dict[str, List[str]]], string_values: Dict[str, Iterable[str]]) -> List[Dict[str, List[str]]]:
    string_placeholder = re.compile(r"<\?STRING>")
    replaced_patterns = []
    for item in patterns_with_non_terminals:
        pattern, non_terminals = item["pattern"], item["non_terminals"]
        if string_placeholder.search(pattern):
            for non_terminal in non_terminals:
                if non_terminal in string_values:
                    for string_value in string_values[non_terminal]:
                        updated_pattern = pattern.replace("<?STRING>", f'"{string_value}"', 1)
                        replaced_patterns.append({"pattern": updated_pattern, "non_terminals": non_terminals})
        else:
            replaced_patterns.append(item)
    return replaced_patterns


def replace_integers(patterns_with_strings: List[Dict[str, List[str]]], int_values: Dict[str, Iterable[str]]) -> List[str]:
    int_placeholder = re.compile(r"<\?INTEGER>")
    final_patterns = []
    for item in patterns_with_strings:
        pattern, non_terminals = item["pattern"], item["non_terminals"]
        if int_placeholder.search(pattern):
            for non_terminal in non_terminals:
                if non_terminal in int_values:
                    for int_value in int_values[non_terminal]:
                        updated_pattern = pattern.replace("<?INTEGER>", int_value, 1)
                        final_patterns.append(updated_pattern)
        else:
            final_patterns.append(pattern)
    return final_patterns


def is_number(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def extract_non_terminal_values(relevant_non_terminals: List[str], initial_inputs: List[FandangoInput]) -> Dict[str, Dict[str, List[str]]]:
    string_values = {}
    int_values = {}
    for non_terminal in relevant_non_terminals:
        for inp in initial_inputs:
            found_trees = inp.tree.find_all_trees(NonTerminal(non_terminal))
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


def learn_constraints_from_inputs(patterns: List[str], initial_inputs: List[FandangoInput], relevant_non_terminals: List[str]) -> List[FandangoConstraintCandidate]:
    # Filter out only failing inputs
    positive_inputs = [inp for inp in initial_inputs if inp.oracle == OracleResult.FAILING]
    # Extract values from non-terminals in failing inputs
    extracted_values = extract_non_terminal_values(relevant_non_terminals, positive_inputs)

    patterns_with_non_terminals = replace_non_terminals(patterns, relevant_non_terminals)
    patterns_with_strings = replace_strings(patterns_with_non_terminals, extracted_values["string_values"])
    final_patterns = replace_integers(patterns_with_strings, extracted_values["int_values"])

    constraints = [parse(pattern)[1][0] for pattern in final_patterns if not re.search(r"<\?([A-Z_]+)>", pattern)]

    candidates = []
    for constraint in constraints:
        candidate = FandangoConstraintCandidate(constraint)
        candidate.evaluate(positive_inputs)
        if candidate.recall() >= 0.8:
            candidates.append(candidate)

    return candidates


if __name__ == "__main__":
    grammar, _ = parse_file('calculator.fan')
    test_inputs = [
        ("sqrt(-900)", OracleResult.FAILING),
        ("sqrt(2)", OracleResult.PASSING),
        ("cos(10)", OracleResult.PASSING),
    ]

    for _ in range(200):
        inp = grammar.fuzz()
        test_inputs.append((str(inp), calculator_oracle(inp)))

    initial_inputs = {FandangoInput.from_str(grammar, inp, result) for inp, result in test_inputs}
    print("Initial inputs:", len(initial_inputs), "(Failing inputs:", len([inp for inp in initial_inputs if inp.oracle == OracleResult.FAILING]), ")", end="\n\n")

    patterns = [
        "int(<?NON_TERMINAL>) <= <?INTEGER>;",
        "str(<?NON_TERMINAL>) == <?STRING>;",
        "int(<?NON_TERMINAL>) == len(str(<?NON_TERMINAL>));"
    ]
    relevant_non_terminals = ["<number>", "<maybeminus>", "<function>"]

    filtered_candidates = learn_constraints_from_inputs(patterns, list(initial_inputs), relevant_non_terminals)

    print("Filtered Atomic Constraints: ")
    for candidate in filtered_candidates:
        candidate.evaluate(initial_inputs)
        print("Constraint:", candidate.constraint, "Recall:", candidate.recall(), "Precision:", candidate.precision())
    print("\n")

    cand1 = filtered_candidates[-1]
    cand2 = filtered_candidates[-2]
    cand3 = cand1 & cand2
    cand3.evaluate(initial_inputs)
    print("Combined Constraints:")
    print("Constraint:", cand3.constraint, "Recall:", cand3.recall(), "Precision:", cand3.precision())

    cand4 = cand1 | cand2
    cand4.evaluate(initial_inputs)
    print("Disjunct Constraints:")
    print("Constraint:", cand4.constraint, "Recall:", cand4.recall(), "Precision:", cand4.precision())
