from typing import List, Dict, Set, Callable
from itertools import product
from copy import deepcopy
import math
import time

from fandango.language.parse import parse, parse_file
from fandangoLearner.data.input import FandangoInput, OracleResult
from fandango.language.symbol import NonTerminal
from fandango.constraints.base import ComparisonConstraint
from fandango.language.search import RuleSearch
from fandangoLearner.learning.candidate import FandangoConstraintCandidate


def is_number(value: str) -> bool:
    """Check if the string can be converted to an integer."""
    try:
        int(value)
        return True
    except ValueError:
        return False


def calculator_oracle(inp: str) -> OracleResult:
    """Evaluate the input expression and return the OracleResult."""
    try:
        eval(inp, {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan})
    except ValueError:
        return OracleResult.FAILING
    return OracleResult.PASSING


class ConstraintLearner:
    """
    A class to encapsulate the constraint learning process.
    """

    def __init__(
        self,
        patterns: List[str],
        initial_inputs: Set[FandangoInput],
        non_terminal_values: Set[NonTerminal],
        threshold: float = 0.8,
    ):
        self.patterns = patterns
        self.initial_inputs = initial_inputs
        self.non_terminal_values = non_terminal_values
        self.threshold = threshold
        self.initialized_patterns = set()
        self.extracted_values = {}
        self.replaced_patterns = []
        self.candidates = []

    def initialize_patterns(self):
        """Parse and initialize constraint patterns."""
        self.initialized_patterns = {parse(pattern)[1][0] for pattern in self.patterns}

    def extract_non_terminal_values(self):
        """Extract values associated with non-terminals from initial inputs."""
        string_values: Dict[NonTerminal, Set[str]] = {}
        int_values: Dict[NonTerminal, Set[str]] = {}

        for non_terminal in self.non_terminal_values:
            for inp in self.initial_inputs:
                found_trees = inp.tree.find_all_trees(non_terminal)
                for tree in found_trees:
                    value = str(tree)
                    if is_number(value):
                        int_values.setdefault(non_terminal, set()).add(value)
                    else:
                        string_values.setdefault(non_terminal, set()).add(value)

        self.extracted_values = {
            "string_values": {k: list(v) for k, v in string_values.items()},
            "int_values": {k: list(v) for k, v in int_values.items()},
        }

    def replace_non_terminals(self):
        """Replace <NON_TERMINAL> placeholders with actual non-terminal values."""
        self.replaced_patterns = []
        for pattern in self.initialized_patterns:
            matches = [
                key
                for key in pattern.searches.keys()
                if pattern.searches[key].symbol == NonTerminal("<NON_TERMINAL>")
            ]
            if matches:
                for replacements in product(self.non_terminal_values, repeat=len(matches)):
                    new_searches = deepcopy(pattern.searches)
                    for key, replacement in zip(matches, replacements):
                        new_searches[key] = RuleSearch(replacement)
                    new_pattern = ComparisonConstraint(
                        operator=pattern.operator,
                        left=pattern.left,
                        right=pattern.right,
                        searches=new_searches,
                        local_variables=pattern.local_variables,
                        global_variables=pattern.global_variables,
                    )
                    self.replaced_patterns.append((new_pattern, set(replacements)))
            else:
                self.replaced_patterns.append((pattern, set()))

    def replace_placeholders(
        self,
        placeholder: NonTerminal,
        values: Dict[NonTerminal, List[str]],
        format_value: Callable[[str], str],
    ):
        """Replace placeholders like <STRING> or <INTEGER> with actual values."""
        new_patterns = []
        for pattern, non_terminals in self.replaced_patterns:
            matches = [
                key
                for key in pattern.searches.keys()
                if pattern.searches[key].symbol == placeholder
            ]
            if matches:
                for non_terminal in non_terminals:
                    for value in values.get(non_terminal, []):
                        updated_right = pattern.right
                        for match in matches:
                            updated_right = updated_right.replace(match, format_value(value), 1)
                        new_searches = deepcopy(pattern.searches)
                        for match in matches:
                            del new_searches[match]
                        new_pattern = ComparisonConstraint(
                            operator=pattern.operator,
                            left=pattern.left,
                            right=updated_right,
                            searches=new_searches,
                            local_variables=pattern.local_variables,
                            global_variables=pattern.global_variables,
                        )
                        new_patterns.append((new_pattern, non_terminals))
            else:
                new_patterns.append((pattern, non_terminals))
        self.replaced_patterns = new_patterns

    def generate_candidates(self):
        """Generate constraint candidates based on the replaced patterns."""
        for pattern, _ in self.replaced_patterns:
            candidate = FandangoConstraintCandidate(pattern)
            try:
                candidate.evaluate(self.initial_inputs)
                if candidate.recall() >= self.threshold:
                    self.candidates.append(candidate)
            except Exception:
                continue

    def learn_constraints(self) -> List[FandangoConstraintCandidate]:
        """Run the entire constraint learning process."""
        self.initialize_patterns()
        self.extract_non_terminal_values()
        self.replace_non_terminals()
        self.replace_placeholders(
            NonTerminal("<STRING>"),
            self.extracted_values["string_values"],
            lambda x: f"'{x}'",
        )
        self.replace_placeholders(
            NonTerminal("<INTEGER>"),
            self.extracted_values["int_values"],
            lambda x: x,
        )
        self.generate_candidates()
        return self.candidates


if __name__ == "__main__":
    grammar, _ = parse_file("calculator.fan")
    test_inputs = [
        ("sqrt(-900)", OracleResult.FAILING),
        ("sqrt(-1)", OracleResult.FAILING),
        ("sin(-900)", OracleResult.PASSING),
        ("sqrt(2)", OracleResult.PASSING),
        ("cos(10)", OracleResult.PASSING),
    ]

    initial_inputs = {
        FandangoInput.from_str(grammar, inp, result) for inp, result in test_inputs
    }

    patterns = [
        "int(<NON_TERMINAL>) <= <INTEGER>;",
        "int(<NON_TERMINAL>) == <INTEGER>;",
        "str(<NON_TERMINAL>) == <STRING>;",
        "int(<NON_TERMINAL>) == len(str(<NON_TERMINAL>));",
        "int(<NON_TERMINAL>) == int(<NON_TERMINAL>) * <INTEGER> * int(<NON_TERMINAL>) * <INTEGER>;",
    ]

    non_terminal_values = {
        NonTerminal("<number>"),
        NonTerminal("<maybeminus>"),
        NonTerminal("<function>"),
    }

    learner = ConstraintLearner(patterns, initial_inputs, non_terminal_values)
    start_time = time.time()
    candidates = learner.learn_constraints()
    end_time = time.time()

    print(f"Time taken to learn constraints: {end_time - start_time:.2f} seconds")
    print("Filtered Learned Atomic Constraints:")
    for candidate in candidates:
        candidate.evaluate(initial_inputs)
        print(
            f"Constraint: {candidate.constraint}, Recall: {candidate.recall()}, Precision: {candidate.precision()}"
        )