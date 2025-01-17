import unittest
from pathlib import Path

from fandangoLearner.data.input import FandangoInput
from fandangoLearner.interface.fandango import parse_file, parse_constraint
from fandangoLearner.learning.candidate import FandangoConstraintCandidate
from fandangoLearner.learning.combination import ConjunctionProcessor


class TestConjunctionProcessor(unittest.TestCase):
    def setUp(self):
        file = Path("tests/resources/calculator.fan")
        self.grammar, self.constraints = parse_file(file)

        # Set up a ConjunctionProcessor with constraints
        self.processor = ConjunctionProcessor(max_conjunction_size=3, min_precision=0.6, min_recall=0.9)

        test_inputs = [
            ("sqrt(-1)",True),
            ("sqrt(-900)",True),
            ("sqrt(3)", False),
            ("cos(3)", False),
            ("sin(-1)", False),
        ]
        self.test_inputs = [FandangoInput.from_str(self.grammar, inp, res) for inp, res in test_inputs]

        self.candidate1 = FandangoConstraintCandidate(self.constraints[0])
        self.candidate2 = FandangoConstraintCandidate(parse_constraint("str(<function>) == 'cos';"))
        self.candidate3 = FandangoConstraintCandidate(parse_constraint("int(<number>) <= -1;"))

        for candidate in [self.candidate1, self.candidate2, self.candidate3]:
            candidate.evaluate(self.test_inputs)

    def test_process_no_valid_conjunctions_due_to_low_recall(self):
        candidates = {self.candidate1, self.candidate2}
        result = self.processor.process(candidates)
        self.assertEqual(len(result), 0)

    def test_process_single_valid_conjunction(self):
        candidates = {self.candidate1, self.candidate2, self.candidate3}

        result = self.processor.process(candidates)
        self.assertEqual(len(result), 1)

    def test_get_possible_conjunctions(self):
        # Test the generation of possible conjunctions
        candidates = {self.candidate1, self.candidate2, self.candidate3}
        result = self.processor.get_possible_conjunctions(candidates)
        for cand in result:
            print(cand)
        expected_combination_count = 4  # C(1, 2), C(1, 3), C(2, 3), C(1, 2, 3)
        self.assertEqual(len(result), expected_combination_count)

    # def test_is_new_conjunction_valid(self):
    #     # Test the validation of a new conjunction
    #     conjunction = MagicMock(spec=FandangoConstraintCandidate, precision=MagicMock(return_value=0.7))
    #     combination = (self.candidate1, self.candidate2)
    #     result = self.processor.is_new_conjunction_valid(conjunction, combination)
    #     self.assertTrue(result)
    #
    # def test_is_new_conjunction_invalid_due_to_low_precision(self):
    #     # Conjunction precision lower than required min_precision
    #     conjunction = MagicMock(spec=FandangoConstraintCandidate, precision=MagicMock(return_value=0.4))
    #     combination = (self.candidate1, self.candidate2)
    #     result = self.processor.is_new_conjunction_valid(conjunction, combination)
    #     self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()