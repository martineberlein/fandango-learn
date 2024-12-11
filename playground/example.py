from typing import List, Dict
import re
from enum import Enum
from itertools import product
from typing import List, Dict, Iterable

from fandango.language.parse import parse_file

from fandangoLearner.learner import BaseFandangoLearner
from fandangoLearner.input import FandangoInput, OracleResult
from fandango.language.symbol import NonTerminal
from fandango.language.parse import parse


def get_constraint(constraint):
    _, constraints = parse(constraint)
    return constraints[0]


class PlaceholderVariable(Enum):
    NON_TERMINAL_PLACEHOLDER = "NON_TERMINAL"
    STRING_PLACEHOLDER = "STRING"
    INTEGER_PLACEHOLDER = "INTEGER"

    def __str__(self):
        return self.value


def replace_non_terminals(patterns: List[str], non_terminal_values: Iterable[str]) -> List[Dict[str, List[str]]]:
    """
    Replace <?NON_TERMINAL> placeholders with provided values.

    :param patterns: List of patterns containing <?NON_TERMINAL> placeholders.
    :param non_terminal_values: Values to replace <?NON_TERMINAL>.
    :return: A list of dictionaries with updated patterns and used non-terminals.
    """
    non_terminal_placeholder = re.compile(r"<\?NON_TERMINAL>")
    replaced_patterns = []

    for pattern in patterns:
        matches = non_terminal_placeholder.findall(pattern)
        if matches:
            # Generate all combinations of non-terminal replacements
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
    """
    Replace <?STRING> placeholders with values based on the used non-terminals.

    :param patterns_with_non_terminals: List of dictionaries with patterns and used non-terminals.
    :param string_values: Mapping of non-terminal values to valid strings.
    :return: A list of dictionaries with updated patterns and associated non-terminals.
    """
    string_placeholder = re.compile(r"<\?STRING>")
    replaced_patterns = []

    for item in patterns_with_non_terminals:
        pattern, non_terminals = item["pattern"], item["non_terminals"]
        if string_placeholder.search(pattern):
            for non_terminal in non_terminals:
                if non_terminal in string_values:
                    for string_value in string_values[non_terminal]:
                        string_value = f'"{string_value}"'
                        updated_pattern = pattern.replace("<?STRING>", string_value, 1)
                        replaced_patterns.append({"pattern": updated_pattern, "non_terminals": non_terminals})
        else:
            replaced_patterns.append(item)

    return replaced_patterns


def replace_integers(patterns_with_strings: List[Dict[str, List[str]]], int_values: Dict[str, Iterable[str]]) -> List[str]:
    """
    Replace <?INTEGER> placeholders with values based on the used non-terminals.

    :param patterns_with_strings: List of dictionaries with patterns and used non-terminals.
    :param int_values: Mapping of non-terminal values to valid integers.
    :return: A list of fully instantiated patterns.
    """
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
    """
    Check if a string represents a valid integer, including negative values.
    :param value: The string to check.
    :return: True if the string is a valid integer, otherwise False.
    """
    try:
        int(value)  # Try converting to an integer
        return True
    except ValueError:
        return False


def extract_non_terminal_values(
    relevant_non_terminals: List[str],
    initial_inputs: List,
) -> Dict[str, Dict[str, List[str]]]:
    """
    Extract values for relevant non-terminals and separate them into string and integer categories.

    :param relevant_non_terminals: List of non-terminal symbols to process.
    :param initial_inputs: List of input trees to extract values from.
    :return: A dictionary containing string and integer values for each non-terminal.
    """
    string_values = {}
    int_values = {}

    for non_terminal in relevant_non_terminals:
        for inp in initial_inputs:
            # Extract all trees corresponding to the current non-terminal
            found_trees = inp.tree.find_all_trees(NonTerminal(non_terminal))
            for tree in found_trees:
                value = str(tree)  # Extract the value as a string
                if is_number(value):  # Check if it's an integer
                    int_values.setdefault(non_terminal, []).append(value)
                else:
                    string_values.setdefault(non_terminal, []).append(value)

    # Remove duplicates by converting lists to sets and back
    string_values = {k: list(set(v)) for k, v in string_values.items()}
    int_values = {k: list(set(v)) for k, v in int_values.items()}

    return {
        "string_values": string_values,
        "int_values": int_values,
    }


from draft2 import replace_non_terminals, replace_strings, replace_integers
import re


def learn_constraints(non_terminal_values, string_values, int_values, patterns):
    # Step-wise processing
    patterns_with_non_terminals = replace_non_terminals(patterns, non_terminal_values)
    patterns_with_strings = replace_strings(patterns_with_non_terminals, string_values)
    final_patterns = replace_integers(patterns_with_strings, int_values)

    result = []
    for pattern in final_patterns:
        placeholders = re.findall(r"<\?([A-Z_]+)>", pattern)
        if not placeholders:
            result.append(pattern)

    return result


if __name__ == "__main__":
    # Parse grammar and constraints
    import math

    def calculator_oracle(inp):
        try:
            eval(
                str(inp), {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan}
            )
        except ValueError:
            return OracleResult.FAILING
        return OracleResult.PASSING

    grammar, _ = parse_file('calculator.fan')

    test_inputs = [
        ("sqrt(-900)", OracleResult.FAILING),
        ("sqrt(2)", OracleResult.PASSING),
        ("cos(10)", OracleResult.PASSING),
    ]

    initial_inputs = {FandangoInput.from_str(grammar, inp, result) for inp, result in test_inputs}

    for inp in initial_inputs:
        print(inp)

    from fandango.evolution.algorithm import Fandango

    for _ in range(10):
        # Initialize FANDANGO
        fandango = Fandango(grammar, list(), verbose=True)
        # Evolve solutions
        solutions = fandango.evolve()

        # Print solutions
        for solution in solutions:
            initial_inputs.add(
                FandangoInput(solution, oracle=calculator_oracle(solution)))

    patterns = [
        "int(<?NON_TERMINAL>) <= <?INTEGER>;",
        "str(<?NON_TERMINAL>) == <?STRING>;",
        # "exists <?NON_TERMINAL> in start: str(<?NON_TERMINAL>) == len(<?NON_TERMINAL>;",
        "int(<?NON_TERMINAL>) == len(str(<?NON_TERMINAL>));"
    ]

    # for pattern in patterns:
    #     constraint = get_constraint(pattern)
    #     print(constraint, type(constraint))
    #     print(constraint.searches)
    #     print(type(constraint.searches))
    #     for search in constraint.searches.values():
    #         print(type(search))
    # exit(0)

    relevant_non_terminals = ["<number>", "<maybeminus>", "<function>"]
    positive_inputs = [inp for inp in initial_inputs if inp.oracle == OracleResult.FAILING]
    for inp in initial_inputs:
        print(inp, inp.oracle)
    results = extract_non_terminal_values(relevant_non_terminals, list(positive_inputs)[:10])

    # Display results
    print("String Values:", results["string_values"])
    print("Integer Values:", results["int_values"])

    res = learn_constraints(
        non_terminal_values=relevant_non_terminals,
        string_values=results["string_values"],
        int_values=results["int_values"],
        patterns=patterns,
    )

    print(res)
    fandango_constraints = []
    for pattern in res:
        pat = get_constraint(pattern)
        fandango_constraints.append(pat)

    from fandangoLearner.candidate import FandangoConstraintCandidate

    filtered_candidates = list()
    # filter step using positive_inputs only:
    for constraint in fandango_constraints:
        candidate = FandangoConstraintCandidate(constraint)
        candidate.evaluate(positive_inputs)
        if candidate.recall() >= 0.8:
            print("Constraint: ", candidate.constraint, " achieved recall: ", candidate.recall(), " and precision: ", candidate.precision(), " (only positive inputs)")
            filtered_candidates.append(candidate)

    print("Filtered fandango constraints: ", len(filtered_candidates))
    print("Initial inputs: ", len(initial_inputs))
    for candidate in filtered_candidates:
        candidate.evaluate(initial_inputs)
        print("Constraint: ", candidate.constraint, " achieved recall: ", candidate.recall(), " and precision: ", candidate.precision())
