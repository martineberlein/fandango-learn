import unittest

from fandango.language.parse import parse
from fandango.constraints.base import (
    ComparisonConstraint,
    ConjunctionConstraint,
    ExistsConstraint, ForallConstraint, ExpressionConstraint,
)
from fandango.language.search import RuleSearch, AttributeSearch

from fdlearn.interface import parse_constraint
from fdlearn.learning.instantiation import NonTerminalPlaceholderTransformer
from fdlearn.reduction.feature_class import get_direct_reachability_map

from .utils import RESOURCES_ROOT


class TestPatternInstantiation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(RESOURCES_ROOT / "calculator.fan", "r") as f:
            cls.grammar, _ = parse(f, use_cache=False, use_stdlib=False)

        relevant_non_terminals = set(cls.grammar.rules.keys())
        reachability_map = get_direct_reachability_map(cls.grammar)
        cls.non_terminal_transformer = NonTerminalPlaceholderTransformer(
            relevant_non_terminals,
            reachability_map=reachability_map
        )

    def transform_pattern(self, pattern):
        transformed_patterns = self.non_terminal_transformer.transform(pattern)
        self.assertTrue(all(isinstance(p, type(pattern)) for p in transformed_patterns))

        return transformed_patterns

    def test_non_terminal_transformer_1(self):
        pattern = parse_constraint("where int(<NON_TERMINAL>) <= -1")
        transformed_patterns = self.transform_pattern(pattern)

        self.assertEqual(len(transformed_patterns), len(self.grammar.rules))

    def test_non_terminal_transformer_2(self):
        pattern = parse_constraint("where int(<elem>) <= -1")
        transformed_patterns = self.transform_pattern(pattern)

        self.assertEqual(len(transformed_patterns), 1)

        unchanged_pattern = transformed_patterns[0]
        self.assertEqual(str(unchanged_pattern), str(pattern))
        # self.assertEqual(unchanged_pattern.searches, pattern.searches)

    def test_non_terminal_transformer_3(self):
        pattern = parse_constraint(
            "where int(<NON_TERMINAL>) <= -1 and str(<NON_TERMINAL>) == 'a'"
        )
        self.assertIsInstance(pattern, ConjunctionConstraint)

        transformed_patterns = self.transform_pattern(pattern)
        self.assertEqual(len(transformed_patterns), len(self.grammar.rules) ** 2)

    def test_non_terminal_transformer_4(self):
        pattern = parse_constraint(
            "where exists <elem> in <NON_TERMINAL>: int(<elem>) <= -1"
        )
        self.assertIsInstance(pattern, ExistsConstraint)

        transformed_patterns = self.transform_pattern(pattern)
        self.assertEqual(len(transformed_patterns), len(self.grammar.rules))

        for pattern in transformed_patterns:
            self.assertIsInstance(pattern, ExistsConstraint)
            self.assertIsInstance(pattern.statement, ComparisonConstraint)

    def test_non_terminal_transformer_5(self):
        pattern = parse_constraint(
            "where exists <elem> in <NON_TERMINAL>: int(<elem>) <= -1 and str(<elem>) == 'a'"
        )
        self.assertIsInstance(pattern, ExistsConstraint)

        transformed_patterns = self.transform_pattern(pattern)
        self.assertEqual(len(transformed_patterns), len(self.grammar.rules))

        for pattern in transformed_patterns:
            self.assertIsInstance(pattern, ExistsConstraint)
            self.assertIsInstance(pattern.statement, ConjunctionConstraint)
            self.assertIsInstance(pattern.search, RuleSearch)
            self.assertTrue(pattern.search.symbol in list(self.grammar.rules.keys()))

    def test_non_terminal_transformer_6(self):
        pattern = parse_constraint(
            "where forall <elem> in <NON_TERMINAL>: int(<elem>) <= -1 and str(<NON_TERMINAL>) == 'a'"
        )
        self.assertIsInstance(pattern, ForallConstraint)

        transformed_patterns = self.transform_pattern(pattern)
        self.assertEqual(len(transformed_patterns), len(self.grammar.rules)**2)

        for pattern in transformed_patterns:
            self.assertIsInstance(pattern, ForallConstraint)
            self.assertIsInstance(pattern.statement, ConjunctionConstraint)
            self.assertIsInstance(pattern.search, RuleSearch)
            self.assertTrue(pattern.search.symbol in list(self.grammar.rules.keys()))

    def test_non_terminal_transformer_7(self):
        pattern = parse_constraint(
            "where <STRING> in str(<NON_TERMINAL>)"
        )
        self.assertIsInstance(pattern, ExpressionConstraint)

        transformed_patterns = self.transform_pattern(pattern)
        self.assertEqual(len(transformed_patterns), len(self.grammar.rules))

    def test_non_terminal_transformer_8(self):
        pattern = parse_constraint(
            "where exists <elem> in <NON_TERMINAL>: int(<ATTRIBUTE>) <= 1"
        )
        self.assertIsInstance(pattern, ExistsConstraint)

        transformed_patterns = self.transform_pattern(pattern)
        self.assertEqual(len(transformed_patterns), len(self.grammar.rules))

        for pattern in transformed_patterns:
            self.assertIsInstance(pattern, ExistsConstraint)
            self.assertIsInstance(pattern.search, RuleSearch)
            self.assertTrue(pattern.search.symbol in list(self.grammar.rules.keys()))
            bounded_constraint = pattern.statement
            self.assertIsInstance(bounded_constraint, ComparisonConstraint)
            self.assertTrue(all(isinstance(att, AttributeSearch) for att in list(bounded_constraint.searches.values())))


if __name__ == "__main__":
    unittest.main()
