from fandango.language.symbol import NonTerminal

from fdlearn.data import FandangoInput


def _is_string_numeric(value: str) -> tuple[bool, float | None]:
    """
    Safely checks if a string can be converted to a float.

    Returns a tuple of (bool, float or None). This avoids converting twice.
    """
    try:
        return True, float(value)
    except (ValueError, TypeError):
        return False, None


def _find_longest_common_substring(strings: list[str]) -> str:
    """
    Finds the longest common substring among a list of strings.
    """
    if not strings:
        return ""

    shortest_str = min(strings, key=len)
    n = len(shortest_str)

    for length in range(n, 0, -1):
        for start in range(n - length + 1):
            substring = shortest_str[start:start + length]
            if all(substring in s for s in strings):
                return substring
    return ""


class ValueMap:
    """
    Extracts and stores string and numeric values associated with specific
    non-terminals from a set of input data.
    """

    def __init__(self, relevant_non_terminals: set[NonTerminal]):
        """Initializes the storage for non-terminal values."""
        self.relevant_non_terminals = relevant_non_terminals
        self._string_values: dict[NonTerminal, set[str]] = {nt: set() for nt in relevant_non_terminals}
        self._numeric_values: dict[NonTerminal, set[float]] = {nt: set() for nt in relevant_non_terminals}

    @classmethod
    def from_inputs(cls, relevant_non_terminals: set[NonTerminal], inputs: set[FandangoInput]) -> 'ValueMap':
        """
        A factory method to create an instance and populate it from inputs.
        """
        instance = cls(relevant_non_terminals)
        instance._populate_values(inputs)
        return instance

    def _populate_values(self, inputs: set[FandangoInput]) -> None:
        """
        Extracts and categorizes values from inputs for relevant non-terminals.
        This method modifies the instance's state.
        """
        for non_terminal in self.relevant_non_terminals:
            all_values_as_strings = []
            for input_obj in inputs:
                found_trees = input_obj.tree.find_all_trees(non_terminal)
                for tree in found_trees:
                    value_str = str(tree)
                    all_values_as_strings.append(value_str)

                    is_numeric, numeric_val = _is_string_numeric(value_str)
                    if is_numeric:
                        self._numeric_values[non_terminal].add(numeric_val)
                    else:
                        self._string_values[non_terminal].add(value_str)

            if len(all_values_as_strings) > 1:
                lcs = _find_longest_common_substring(all_values_as_strings)
                if len(lcs) >= 2:
                    self._string_values[non_terminal].add(lcs)

    @property
    def string_values(self) -> dict[NonTerminal, set[str]]:
        """Returns all collected string values."""
        return self._string_values

    @property
    def numeric_values(self) -> dict[NonTerminal, set[float]]:
        """Returns all collected numeric values."""
        return self._numeric_values

    @property
    def filtered_numeric_values(self) -> dict[NonTerminal, set[float]]:
        """
        Returns a map containing only the min and max numeric values
        for each non-terminal.
        """
        reduced_values = {}
        for non_terminal, values in self._numeric_values.items():
            if values:
                reduced_values[non_terminal] = {min(values), max(values)}
        return reduced_values