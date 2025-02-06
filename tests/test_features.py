import string
import unittest

from fandango.language.symbol import NonTerminal, Terminal
from numpy import inf
from fandango.language.grammar import Grammar

from fandangoLearner.interface.fandango import parse_contents

from fandangoLearner.data.input import FandangoInput
#from fandangoLearner.reduction.feature_class import Feature, FeatureFactory, ExistenceFeature
from fandangoLearner.reduction.feature_class import (
    FeatureFactory,
    ExistenceFeature,
    DerivationFeature,
    NumericFeature,
    LengthFeature,
    #GrammarFeatureCollector,
)

grammar_ = """
<start> ::= <string>;
<string> ::= <A> | <B> | "!ab!";
<A> ::= "a" | "b" | "c" | "d" | "e";
<B> ::= "0" | "1" | "2" | "3" | "4" ;
"""

grammar, _ = parse_contents(grammar_)

# grammar_rec: Grammar = {
#     "<start>": ["<string>"],
#     "<string>": ["<A>", "<B>", "!ab!"],
#     "<A>": ["<chars><A>", ""],
#     "<chars>": [char for char in string.ascii_lowercase],
#     "<B>": ["<digit><B>", ""],
#     "<digit>": [str(num) for num in range(0, 10)],
# }
# assert is_valid_grammar(grammar_rec)
#
grammar_with_minus_ = """
<start> ::= <string>;
<string> ::= <A> | <B>;
<A> ::= "" | "-";
<B> ::= "0" | "1" | "2" | "3" | "4" ;
"""

grammar_with_maybe_minus, _ = parse_contents(grammar_with_minus_)


class FeatureExtraction(unittest.TestCase):
    def test_build_existence_feature(self):
        expected_feature_list = [
            ExistenceFeature(NonTerminal("<start>")),
            ExistenceFeature(NonTerminal("<string>")),
            ExistenceFeature(NonTerminal("<A>")),
            ExistenceFeature(NonTerminal("<B>")),
        ]

        factory = FeatureFactory(grammar)
        features = factory.build([ExistenceFeature])

        self.assertEqual(features, expected_feature_list)

    def test_build_derivation_feature(self):
        expected_feature_list = [
            DerivationFeature(NonTerminal("<start>"), NonTerminal("<string>")),
            DerivationFeature(NonTerminal("<string>"), NonTerminal("<A>")),
            DerivationFeature(NonTerminal("<string>"), NonTerminal("<B>")),
            DerivationFeature(NonTerminal("<string>"), Terminal("!ab!")),
            DerivationFeature(NonTerminal("<A>"), Terminal("a")),
            DerivationFeature(NonTerminal("<A>"), Terminal("b")),
            DerivationFeature(NonTerminal("<A>"), Terminal("c")),
            DerivationFeature(NonTerminal("<A>"), Terminal("d")),
            DerivationFeature(NonTerminal("<A>"), Terminal("e")),
            DerivationFeature(NonTerminal("<B>"), Terminal("0")),
            DerivationFeature(NonTerminal("<B>"), Terminal("1")),
            DerivationFeature(NonTerminal("<B>"), Terminal("2")),
            DerivationFeature(NonTerminal("<B>"), Terminal("3")),
            DerivationFeature(NonTerminal("<B>"), Terminal("4")),
        ]

        factory = FeatureFactory(grammar)
        features = factory.build([DerivationFeature])

        self.assertEqual(features, expected_feature_list)

    def test_build_numeric_feature(self):
        expected_feature_list = [
            NumericFeature(NonTerminal("<B>")),
        ]

        factory = FeatureFactory(grammar)
        features = factory.build([NumericFeature])

        self.assertEqual(features, expected_feature_list)

    def test_build_numeric_feature_maybe(self):
        # We do not expect num(<A>) as this is not a number
        expected_feature_list = [
            NumericFeature(NonTerminal("<start>")),
            NumericFeature(NonTerminal("<string>")),
            NumericFeature(NonTerminal("<B>")),
        ]

        factory = FeatureFactory(grammar_with_maybe_minus)
        features = factory.build([NumericFeature])

        self.assertEqual(set(features), set(expected_feature_list))

    def test_build_length_feature(self):
        expected_feature_list = [
            LengthFeature(NonTerminal("<start>")),
            LengthFeature(NonTerminal("<string>")),
            LengthFeature(NonTerminal("<A>")),
            LengthFeature(NonTerminal("<B>")),
        ]

        factory = FeatureFactory(grammar)
        features = factory.build([LengthFeature])

        self.assertEqual(features, expected_feature_list)

    def test_parse_existence_feature(self):
        inputs = ["4", "3", "a"]
        test_inputs = [Input.from_str(grammar, inp) for inp in inputs]

        expected_feature_vectors = [
            {
                ExistenceFeature("<start>"): 1,
                ExistenceFeature("<string>"): 1,
                ExistenceFeature("<A>"): 0,
                ExistenceFeature("<B>"): 1,
            },
            {
                ExistenceFeature("<start>"): 1,
                ExistenceFeature("<string>"): 1,
                ExistenceFeature("<A>"): 0,
                ExistenceFeature("<B>"): 1,
            },
            {
                ExistenceFeature("<start>"): 1,
                ExistenceFeature("<string>"): 1,
                ExistenceFeature("<A>"): 1,
                ExistenceFeature("<B>"): 0,
            },
        ]

        collector = GrammarFeatureCollector(grammar, [ExistenceFeature])
        for test_input, expected_feature_vectors in zip(
            test_inputs, expected_feature_vectors
        ):
            feature_vector = collector.collect_features(test_input)
            self.assertEqual(feature_vector.features, expected_feature_vectors)

    def test_parse_numeric_feature(self):
        inputs = ["4", "3", "a"]
        test_inputs = [Input.from_str(grammar, inp) for inp in inputs]

        expected_feature_vectors = [
            {
                NumericFeature("<B>"): 4.0,
            },
            {
                NumericFeature("<B>"): 3.0,
            },
            {
                NumericFeature("<B>"): -inf,
            },
        ]

        collector = GrammarFeatureCollector(grammar, [NumericFeature])
        for test_input, expected_feature_vectors in zip(
            test_inputs, expected_feature_vectors
        ):
            feature_vector = collector.collect_features(test_input)
            self.assertEqual(feature_vector.features, expected_feature_vectors)

    def test_parse_features_length(self):
        inputs = ["4", "3", "a"]
        test_inputs = [Input.from_str(grammar, inp) for inp in inputs]

        expected_feature_vectors = [
            {
                LengthFeature("<start>"): 1,
                LengthFeature("<string>"): 1,
                LengthFeature("<A>"): 0,
                LengthFeature("<B>"): 1,
            },
            {
                LengthFeature("<start>"): 1,
                LengthFeature("<string>"): 1,
                LengthFeature("<A>"): 0,
                LengthFeature("<B>"): 1,
            },
            {
                LengthFeature("<start>"): 1,
                LengthFeature("<string>"): 1,
                LengthFeature("<A>"): 1,
                LengthFeature("<B>"): 0,
            },
        ]

        collector = GrammarFeatureCollector(grammar, [LengthFeature])
        for test_input, expected_feature_vectors in zip(
            test_inputs, expected_feature_vectors
        ):
            feature_vector = collector.collect_features(test_input)
            self.assertEqual(feature_vector.features, expected_feature_vectors)

    def test_parse_numericInterpretation_maybe_minus(self):
        inputs = ["-1", "3", "-9"]
        test_inputs = [Input.from_str(grammar_with_maybe_minus, inp) for inp in inputs]

        expected_feature_vectors = [
            {
                NumericFeature("<start>"): -1.0,
                NumericFeature("<string>"): -1.0,
                NumericFeature("<B>"): 1.0,
            },
            {
                NumericFeature("<start>"): 3.0,
                NumericFeature("<string>"): 3.0,
                NumericFeature("<B>"): 3.0,
            },
            {
                NumericFeature("<start>"): -9.0,
                NumericFeature("<string>"): -9.0,
                NumericFeature("<B>"): 9.0,
            },
        ]

        collector = GrammarFeatureCollector(grammar_with_maybe_minus, [NumericFeature])
        for test_input, expected_feature_vectors in zip(
            test_inputs, expected_feature_vectors
        ):
            feature_vector = collector.collect_features(test_input)
            self.assertEqual(feature_vector.features, expected_feature_vectors)

    def test_parse_features_numericInterpretation_recursive(self):
        inputs = ["11923", "3341923", "9", "a"]
        test_inputs = [Input.from_str(grammar_rec, inp) for inp in inputs]

        expected_feature_vectors = [
            {
                NumericFeature("<digit>"): 9.0,
                NumericFeature("<B>"): 11923.0,
            },
            {
                NumericFeature("<digit>"): 9.0,
                NumericFeature("<B>"): 3341923.0,
            },
            {
                NumericFeature("<digit>"): 9.0,
                NumericFeature("<B>"): 9.0,
            },
            {
                NumericFeature("<digit>"): -inf,
                NumericFeature("<B>"): -inf,
            },
        ]

        collector = GrammarFeatureCollector(grammar_rec, [NumericFeature])
        for test_input, expected_feature_vectors in zip(
            test_inputs, expected_feature_vectors
        ):
            feature_vector = collector.collect_features(test_input)
            self.assertEqual(feature_vector.features, expected_feature_vectors)

    def test_parse_features_length_recursive(self):
        inputs = ["123", "ab"]
        test_inputs = [Input.from_str(grammar_rec, inp) for inp in inputs]

        expected_feature_vectors = [
            {
                LengthFeature("<start>"): 3,
                LengthFeature("<string>"): 3,
                LengthFeature("<A>"): 0,
                LengthFeature("<chars>"): 0,
                LengthFeature("<B>"): 3,
                LengthFeature("<digit>"): 1,
            },
            {
                LengthFeature("<start>"): 2,
                LengthFeature("<string>"): 2,
                LengthFeature("<A>"): 2,
                LengthFeature("<chars>"): 1,
                LengthFeature("<B>"): 0,
                LengthFeature("<digit>"): 0,
            },
        ]

        collector = GrammarFeatureCollector(grammar_rec, [LengthFeature])
        for test_input, expected_feature_vectors in zip(
            test_inputs, expected_feature_vectors
        ):
            feature_vector = collector.collect_features(test_input)
            self.assertEqual(feature_vector.features, expected_feature_vectors)

    def test_build_features_with_escaped_characters(self):
        grammar_with_json_chars = {
            "<start>": ["<arg>"],
            "<arg>": ["<digit>", '"<digit>"'],
            "<digit>": ["1"],
        }
        expected_feature_list = [
            DerivationFeature("<start>", "<arg>"),
            DerivationFeature("<arg>", "<digit>"),
            DerivationFeature("<arg>", '"<digit>"'),
            DerivationFeature("<digit>", "1"),
        ]

        factory = FeatureFactory(grammar_with_json_chars)
        features = factory.build([DerivationFeature])

        self.assertEqual(set(features), set(expected_feature_list))

    def test_feature_names_with_json_chars(self):
        grammar_with_json_chars = {
            "<start>": ["<arg>"],
            "<arg>": ["<digit>", '"<digit>"'],
            "<digit>": ["1"],
        }
        inputs = ["1", '"1"']
        test_inputs = [Input.from_str(grammar_with_json_chars, inp) for inp in inputs]

        expected_feature_vectors = [
            {
                DerivationFeature("<start>", "<arg>"): 1,
                DerivationFeature("<arg>", "<digit>"): 1,
                DerivationFeature("<arg>", '"<digit>"'): 0,
                DerivationFeature("<digit>", "1"): 1,
            },
            {
                DerivationFeature("<start>", "<arg>"): 1,
                DerivationFeature("<arg>", "<digit>"): 0,
                DerivationFeature("<arg>", '"<digit>"'): 1,
                DerivationFeature("<digit>", "1"): 1,
            },
        ]

        collector = GrammarFeatureCollector(
            grammar_with_json_chars, [DerivationFeature]
        )

        for test_input, expected_feature_vectors in zip(
            test_inputs, expected_feature_vectors
        ):
            feature_vector = collector.collect_features(test_input)
            self.assertEqual(feature_vector.features, expected_feature_vectors)


if __name__ == "__main__":
    unittest.main()
