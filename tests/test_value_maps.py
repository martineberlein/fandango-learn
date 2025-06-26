import unittest

from fandango.language.symbol import NonTerminal
from fandango.language.parse import parse

from fdlearn.data.input import FandangoInput
from fdlearn.learning.instantiation import ValueMaps
from .utils import RESOURCES_ROOT


class TestConjunctionProcessor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(RESOURCES_ROOT / "calculator.fan", "r") as grammar:
            cls.grammar, _ = parse(grammar, use_cache=False, use_stdlib=False)

        test_inputs = [
            ("sqrt(-1)", True),
            ("sqrt(-10)", True),
            ("sqrt(-900)", True),
            ("sqrt(3)", False),
            ("cos(3)", False),
            ("sin(-1)", False),
        ]
        cls.test_inputs = {
            FandangoInput.from_str(cls.grammar, inp, res) for inp, res in test_inputs
        }

    def test_value_map(self):
        relevant_non_terminals = {
            NonTerminal("<number>"),
            NonTerminal("<maybeminus>"),
            NonTerminal("<function>"),
        }

        value_map = ValueMaps.from_inputs(
            relevant_non_terminals=relevant_non_terminals, inputs=self.test_inputs
        )

        # Expected results
        expected_int_values = {
            NonTerminal("<number>"): {3, -900, -10, -1},
            NonTerminal("<function>"): set(),
            NonTerminal("<maybeminus>"): set(),
        }
        expected_string_values = {
            NonTerminal("<number>"): set(),
            NonTerminal("<maybeminus>"): {"-", ""},
            NonTerminal("<function>"): {"sin", "sqrt", "cos"},
        }

        self.assertEqual(value_map.numeric_values, expected_int_values)
        self.assertEqual(value_map.string_values, expected_string_values)

    def test_value_map_min_max(self):
        relevant_non_terminals = {
            NonTerminal("<number>"),
            NonTerminal("<maybeminus>"),
            NonTerminal("<function>"),
        }

        value_map = ValueMaps.from_inputs(
            relevant_non_terminals=relevant_non_terminals, inputs=self.test_inputs
        )

        self.assertEqual(
            value_map.filtered_numeric_values,
            {
                NonTerminal("<number>"): {3, -900},
            },
        )

    def test_large_input_size(self):
        test_inputs = set()
        for _ in range(1000):
            test_inputs.add(FandangoInput(self.grammar.fuzz()))

        relevant_non_terminals = {
            NonTerminal("<number>"),
            NonTerminal("<maybeminus>"),
            NonTerminal("<function>"),
        }

        value_map = ValueMaps.from_inputs(
            relevant_non_terminals=relevant_non_terminals, inputs=test_inputs
        )

        function_values = value_map.string_values[NonTerminal("<function>")]
        reduced_int_values = value_map.filtered_numeric_values

        self.assertEqual(len(function_values), 4)
        self.assertEqual(len(reduced_int_values[NonTerminal("<number>")]), 2)


if __name__ == "__main__":
    unittest.main()
