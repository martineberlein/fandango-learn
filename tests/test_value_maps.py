import unittest
import os

from fandango.language.symbol import NonTerminal

from fandangoLearner.data.input import FandangoInput
from fandangoLearner.interface.fandango import parse_file
from fandangoLearner.learning.instantiation import ValueMaps


class TestConjunctionProcessor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base_path = os.path.dirname(__file__)

    def setUp(self):
        file = os.path.join(self.base_path, "resources", "calculator.fan")
        self.grammar, _ = parse_file(file)

        test_inputs = [
            ("sqrt(-1)",True),
            ("sqrt(-10)", True),
            ("sqrt(-900)",True),
            ("sqrt(3)", False),
            ("cos(3)", False),
            ("sin(-1)", False),
        ]
        self.test_inputs = {FandangoInput.from_str(self.grammar, inp, res) for inp, res in test_inputs}

    def test_value_map(self):
        relevant_non_terminals = {
            NonTerminal("<number>"),
            NonTerminal("<maybeminus>"),
            NonTerminal("<function>"),
        }

        value_map = ValueMaps(relevant_non_terminals)
        value_map.calculate_non_terminal_values(self.test_inputs)

        # Expected results
        expected_int_values = {
            NonTerminal("<number>"): {3, -900, -10, -1},
            NonTerminal("<function>"): set(),
            NonTerminal("<maybeminus>"): set(),
        }
        expected_string_values = {
            NonTerminal("<number>"): set(),
            NonTerminal("<maybeminus>"): {"-", ""},
            NonTerminal("<function>"): {"sin", "sqrt", "cos"}
        }

        # Verify integer values are extracted correctly
        self.assertEqual(value_map.get_int_values(), expected_int_values)

        # Verify string values are extracted correctly
        self.assertEqual(value_map.get_string_values(), expected_string_values)

    def test_value_map_min_max(self):
        relevant_non_terminals = {
            NonTerminal("<number>"),
            NonTerminal("<maybeminus>"),
            NonTerminal("<function>"),
        }
        value_map = ValueMaps(relevant_non_terminals)
        value_map.calculate_non_terminal_values(self.test_inputs)

        result = value_map.get_filtered_int_values()
        self.assertEqual(
            result,
            {
                NonTerminal("<number>"): { 3, -900},
            }
        )

    def test_large_input_size(self):
        test_inputs = set()
        for _ in range(10000):
            test_inputs.add(FandangoInput(self.grammar.fuzz()))

        relevant_non_terminals = {
            NonTerminal("<number>"),
            NonTerminal("<maybeminus>"),
            NonTerminal("<function>"),
        }
        value_map = ValueMaps(relevant_non_terminals)
        string_values = value_map.calculate_non_terminal_values(test_inputs)
        print(string_values)
        red = value_map.get_filtered_int_values()
        print(red)

if __name__ == '__main__':
    unittest.main()