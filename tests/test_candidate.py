import unittest

from fandango.constraints.base import ConjunctionConstraint
from fandango.evolution.algorithm import Fandango

from fdlearn.data import FandangoInput, OracleResult
from fdlearn.language.constraints import NegationConstraint
from fdlearn.learning.candidate import FandangoConstraintCandidate, CandidateSet
from fdlearn.interface.fandango import parse_contents, parse_constraint


class TestFandangoConstraintCandidate(unittest.TestCase):

    GRAMMAR = """
        <start> ::= <arithexp>;
        <arithexp> ::= <function>"("<number>")";
        <function> ::= "sqrt" | "cos" | "sin" | "tan";
        <number> ::= <maybeminus><onenine><maybedigits> | "0";
        <maybeminus> ::= "-" | "";
        <onenine> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
        <maybedigits> ::= <digit>*;
        <digit>::=  "0" | <onenine>;
    """

    def setUp(self):
        grammar, constraints = parse_contents(
            self.GRAMMAR + "(int(<number>) <= -10 and str(<function>) == 'sqrt');",
        )
        self.constraint = constraints[0]
        self.grammar = grammar

        # Create mock derivation trees
        self.failing_input = FandangoInput.from_str(
            self.grammar, "sqrt(-900)", OracleResult.FAILING
        )
        self.passing_input = FandangoInput.from_str(
            self.grammar, "sqrt(1)", OracleResult.PASSING
        )

        # Instantiate the candidate with the mock constraint
        self.candidate = FandangoConstraintCandidate(self.constraint)

    def test_evaluate(self):
        inputs = [self.failing_input, self.passing_input]
        self.candidate.evaluate(inputs)

        # Check if evaluation results are recorded correctly
        self.assertEqual(self.candidate.failing_inputs_eval_results, [True])
        self.assertEqual(self.candidate.passing_inputs_eval_results, [False])

        for key, value in self.candidate.cache.items():
            self.assertEqual(key.oracle.is_failing(), value)

    def test_many_evaluate(self):
        inputs = []
        for _ in range(100):
                inputs.append(FandangoInput.from_str(
                    self.grammar, "sqrt(-900)", OracleResult.FAILING
                ))

        for _ in range(10):
            self.candidate = FandangoConstraintCandidate(self.constraint)
            self.candidate.evaluate(inputs)

    def test_precision(self):
        inputs = [self.failing_input, self.passing_input]
        self.candidate.evaluate(inputs)

        # Precision = TP / (TP + FP)
        precision = self.candidate.precision()
        self.assertEqual(precision, 1.0)

    def test_recall(self):
        inputs = [self.failing_input, self.passing_input]
        self.candidate.evaluate(inputs)

        # Recall = TP / (TP + FN)
        recall = self.candidate.recall()
        self.assertEqual(recall, 1.0)

    def test_specificity(self):
        inputs = [self.failing_input, self.passing_input]
        self.candidate.evaluate(inputs)

        # Specificity = TN / (TN + FP)
        specificity = self.candidate.specificity()
        self.assertEqual(specificity, 1.0)

    def test_and_operator(self):
        # Create another candidate with a similar constraint
        candidate = FandangoConstraintCandidate(parse_constraint("int(<number>) <= 0;"))
        other_candidate = FandangoConstraintCandidate(
            parse_constraint("str(<function>) == 'sqrt';")
        )

        # Evaluate both candidates
        candidate.evaluate([self.failing_input, self.passing_input])
        other_candidate.evaluate([self.failing_input, self.passing_input])

        self.assertLess(other_candidate.precision(), 1.0)

        # Combine them with AND
        combined_candidate = candidate & other_candidate

        # Verify the combined constraint evaluates correctly
        self.assertEqual(combined_candidate.failing_inputs_eval_results, [True])
        self.assertEqual(combined_candidate.passing_inputs_eval_results, [False])

        for key, value in self.candidate.cache.items():
            self.assertEqual(key.oracle.is_failing(), value)

        self.assertEqual(combined_candidate.precision(), 1.0)
        self.assertEqual(combined_candidate.recall(), 1.0)

    def test_or_operator(self):
        # Create another candidate with a different constraint
        candidate = FandangoConstraintCandidate(parse_constraint("int(<number>) <= 0;"))
        other_candidate = FandangoConstraintCandidate(
            parse_constraint("str(<function>) == 'sqrt';")
        )

        # Evaluate both candidates
        candidate.evaluate([self.failing_input, self.passing_input])
        other_candidate.evaluate([self.failing_input, self.passing_input])

        # Combine them with OR
        combined_candidate = candidate | other_candidate

        # Verify the combined constraint evaluates correctly
        self.assertEqual(combined_candidate.failing_inputs_eval_results, [True])
        self.assertEqual(combined_candidate.passing_inputs_eval_results, [True])

        # Not a perfect constraint
        self.assertEqual(combined_candidate.cache[self.failing_input], True)
        self.assertEqual(combined_candidate.cache[self.passing_input], True)

    def test_negation(self):
        candidate = FandangoConstraintCandidate(parse_constraint("int(<number>) <= 0;"))
        candidate.evaluate([self.failing_input, self.passing_input])
        self.assertEqual(candidate.cache[self.failing_input], True)
        self.assertEqual(candidate.cache[self.passing_input], False)

        negated_candidate = -candidate
        self.assertEqual(negated_candidate.precision(), 0.0)
        self.assertEqual(negated_candidate.recall(), 0.0)

        self.assertEqual(negated_candidate.cache[self.failing_input], False)
        self.assertEqual(negated_candidate.cache[self.passing_input], True)

    def test_reset(self):
        inputs = [self.failing_input, self.passing_input]
        self.candidate.evaluate(inputs)

        # Reset the candidate
        self.candidate.reset()

        # Check if results are cleared
        self.assertEqual(self.candidate.failing_inputs_eval_results, [])
        self.assertEqual(self.candidate.passing_inputs_eval_results, [])
        self.assertEqual(self.candidate.cache, {})

    def test_str_representation(self):
        inputs = [self.failing_input, self.passing_input]
        self.candidate.evaluate(inputs)

        # Check if string representation includes precision and recall
        representation = str(self.candidate)
        self.assertIn("Precision: 1.0", representation)
        self.assertIn("Recall: 1.0", representation)

    def test_constraint_with_missing_non_terminals(self):
        candidate = FandangoConstraintCandidate(
            parse_constraint("str(<maybeminus>) == '-';")
        )
        null_input = FandangoInput.from_str(
            self.grammar, "sqrt(0)", OracleResult.PASSING
        )

        # Evaluate both candidates
        candidate.evaluate([null_input, self.failing_input])

        # sqrt(0) does not contain a '-', but it does also not contain a <maybeminus> non-terminal.
        # Thus, the constraint should evaluate to True
        self.assertEqual(candidate.precision(), 0.5)
        self.assertEqual(candidate.recall(), 1.0)

        self.assertEqual(candidate.cache[null_input], True)
        self.assertEqual(candidate.cache[self.failing_input], True)

    def test_candidate_hash(self):
        inputs = [self.failing_input, self.passing_input]
        self.candidate.evaluate(inputs)

        candidates = set()
        candidates.add(self.candidate)
        candidates.add(self.candidate)
        candidates.add(self.candidate)
        self.assertEqual(len(candidates), 1)

        self.assertTrue(self.candidate in candidates)
        self.assertFalse(self.candidate not in candidates)

    def test_candidate_set(self):
        inputs = [self.failing_input, self.passing_input]
        self.candidate.evaluate(inputs)
        candidate_set = CandidateSet()
        candidate_set.append(self.candidate)
        self.assertTrue(self.candidate in candidate_set)
        self.assertFalse(self.candidate not in candidate_set)

        candidate_set.append(self.candidate)
        self.assertEqual(len(candidate_set), 1)

        candidate_set.remove(self.candidate)
        self.assertEqual(len(candidate_set), 0)
        self.assertEqual(len(candidate_set.candidate_hashes), 0)

    def test_iterate_candidate_set(self):
        inputs = [self.failing_input, self.passing_input]
        self.candidate.evaluate(inputs)
        candidate_set = CandidateSet([self.candidate])
        for candidate in candidate_set:
            self.assertEqual(candidate, self.candidate)

    def test_candidate_set_append(self):
        inputs = [self.failing_input, self.passing_input]
        self.candidate.evaluate(inputs)

        candidate_set = CandidateSet()
        candidate_set.append(self.candidate)
        self.assertEqual(len(candidate_set), 1)
        self.assertTrue(self.candidate in candidate_set)
        self.assertFalse(self.candidate not in candidate_set)

        candidate_set.append(self.candidate)
        self.assertEqual(len(candidate_set), 1)

    def test_candidate_set_instantiation(self):
        inputs = [self.failing_input, self.passing_input]
        self.candidate.evaluate(inputs)

        candidate_set = CandidateSet([self.candidate])
        self.assertEqual(len(candidate_set), 1)
        self.assertTrue(self.candidate in candidate_set)
        self.assertFalse(self.candidate not in candidate_set)

    def test_negation_fuzzing(self):
        candidate = FandangoConstraintCandidate(parse_constraint("int(<number>) <= 0;"))
        candidate.evaluate([self.failing_input, self.passing_input])
        self.assertEqual(candidate.cache[self.failing_input], True)
        self.assertEqual(candidate.cache[self.passing_input], False)

        negated_candidate = NegationConstraint(candidate.constraint)
        candidate2 = FandangoConstraintCandidate(
            parse_constraint("str(<function>) == 'sqrt';")
        )
        test_constraint = ConjunctionConstraint(
            [negated_candidate, candidate2.constraint]
        )
        # print(negated_candidate.check(self.failing_input.tree))
        print(test_constraint)

        # initial = []
        # for _ in range(100):
        #     initial.append(self.grammar.fuzz())
        fandango = Fandango(
            grammar=self.grammar,
            constraints=[negated_candidate],
            desired_solutions=100,
            random_seed=1,
            # initial_population=initial,
        )
        results = fandango.evolve()
        solutions = set()
        for inp in results:
            solutions.add(FandangoInput(inp))

        print(solutions)


if __name__ == "__main__":
    unittest.main()
