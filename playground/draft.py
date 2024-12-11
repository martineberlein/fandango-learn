import re
from enum import Enum
from itertools import product, permutations
from typing import List, Dict, Iterable


class PlaceholderVariable(Enum):
    NON_TERMINAL_PLACEHOLDER = "NON_TERMINAL"
    STRING_PLACEHOLDER = "STRING"
    INTEGER_PLACEHOLDER = "INTEGER"
    BOOLEAN_PLACEHOLDER = "BOOLEAN"

    def __str__(self):
        return self.value

def instantiate_string_patterns(
    patterns: List[str],
    instantiations: Dict[PlaceholderVariable, Iterable[str]],
    searches: Dict[str, Iterable[str]]
) -> List[str]:
    """
    Instantiate string patterns by replacing placeholders with valid values.

    :param patterns: List of patterns with placeholders (e.g., "<?NON_TERMINAL>", "<?INTEGER>").
    :param instantiations: Dictionary mapping PlaceholderVariable to valid replacement values.
    :param searches: Mapping of NON_TERMINAL values to constraints for related placeholders.
    :return: List of fully instantiated patterns.
    """
    placeholder_to_regex = {ph: f"<\\?{ph.value}>" for ph in PlaceholderVariable}
    instantiated_patterns = []

    for pattern in patterns:
        # Find placeholders in the pattern
        placeholders = re.findall(r"<\?([A-Z_]+)>", pattern)

        if not placeholders:
            instantiated_patterns.append(pattern)
            continue

        # Collect possible replacements for each placeholder in the pattern
        replacements = {}
        for ph in placeholders:
            if ph == "NON_TERMINAL":
                replacements[ph] = instantiations[PlaceholderVariable.NON_TERMINAL_PLACEHOLDER]
            elif ph == "INTEGER" or ph == "STRING":
                replacements[ph] = instantiations[PlaceholderVariable[ph + "_PLACEHOLDER"]]

        # Generate combinations of NON_TERMINAL with related constraints from searches
        non_terminal_replacements = replacements.get("NON_TERMINAL", [])
        final_combinations = []

        for non_terminal in non_terminal_replacements:
            constrained_replacements = {**replacements}  # Copy replacements
            cp = dict()
            if non_terminal in searches:
                if "INTEGER" in placeholders:
                    cp["INTEGER"] = searches[non_terminal]
                if "STRING" in placeholders:
                    cp["STRING"] = searches[non_terminal]

            # Compute combinations for this NON_TERMINAL
            # current_combinations = list(product(*[constrained_replacements[ph] for ph in placeholders]))
            for rep in cp.values():
                final_combinations.append((non_terminal, rep))


        print("final combinations: ",  final_combinations)
        # Replace placeholders in the pattern for each valid combination
        for non_terminal, combination in final_combinations:
            print(non_terminal, combination)
            instantiated_pattern = pattern
            for ph, value in product(placeholders, combination):
                if ph == "NON_TERMINAL":
                    instantiated_pattern = instantiated_pattern.replace(f"<?{ph}>", non_terminal, 1)
                else:
                    instantiated_pattern = instantiated_pattern.replace(f"<?{ph}>", value, 1)
            print(instantiated_pattern)
            instantiated_patterns.append(instantiated_pattern)

    return instantiated_patterns


if __name__ == "__main__":

    # Example usage
    patterns = [
        "int(<?NON_TERMINAL>) <= <?INTEGER>",
        "str(<?NON_TERMINAL>) == <?STRING>",
    ]

    instantiations = {
        PlaceholderVariable.NON_TERMINAL_PLACEHOLDER: ["<x>", "<y>", "<function>"],
        PlaceholderVariable.INTEGER_PLACEHOLDER: ["10", "20", "30"],
        PlaceholderVariable.STRING_PLACEHOLDER: ["sqrt", "log"],
    }

    searches = {
        "<x>": ["4", "3", "1"],
        "<y>": ["10", "30"],
        "<function>": ["sqrt", "log"],
    }

    result = instantiate_string_patterns(patterns, instantiations, searches)
    print(result)

