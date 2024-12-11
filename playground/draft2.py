import re
from enum import Enum
from itertools import product
from typing import List, Dict, Iterable

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


if __name__ == "__main__":
    # Initial patterns with placeholders
    patterns = [
        "int(<?NON_TERMINAL>) <= <?INTEGER>",
        "str(<?NON_TERMINAL>) == <?STRING>",
        "exists <?NON_TERMINAL> such that int(<?STRING>) == <?INTEGER>",
        "str(<?NON_TERMINAL>) == len(<?NON_TERMINAL>)",
    ]

    # Placeholder values
    non_terminal_values = ["<x>", "<y>", "<function>"]
    string_values = {
        # "<x>": ["foo", "bar"],
        "<y>": ["10"],
        "<function>": ["sqrt", "log"],
    }
    int_values = {
        "<x>": ["1", "2"],
        "<y>": ["10", "20"],
        # "<function>": ["30", "40"],
    }

    # Step-wise processing
    patterns_with_non_terminals = replace_non_terminals(patterns, non_terminal_values)
    patterns_with_strings = replace_strings(patterns_with_non_terminals, string_values)
    final_patterns = replace_integers(patterns_with_strings, int_values)

    result = []
    for pattern in final_patterns:
        placeholders = re.findall(r"<\?([A-Z_]+)>", pattern)
        if not placeholders:
            result.append(get_constraint(pattern))

