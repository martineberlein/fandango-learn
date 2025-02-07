from functools import lru_cache
from typing import List, Dict, Optional, Any, Type
from abc import ABC, abstractmethod

# from debugging_framework.fuzzingbook.grammar import is_nonterminal, Grammar
# from isla.language import DerivationTree

from fandango.language.grammar import Grammar
from fandango.language.symbol import NonTerminal, Symbol
from fandango.language.tree import DerivationTree

from fandangoLearner.data.input import FandangoInput
from fandangoLearner.reduction.feature_class import (
    Feature,
    ExistenceFeature,
    DerivationFeature,
    NumericFeature,
    LengthFeature,
    FeatureFactory,
    FeatureVector,
)


DEFAULT_FEATURE_TYPES: List[Type[Feature]] = [
    ExistenceFeature,
    DerivationFeature,
    NumericFeature,
    LengthFeature,
]


class FeatureCollector(ABC):
    def __init__(
        self, grammar: Grammar, feature_types: Optional[List[Type[Feature]]] = None
    ):
        self.grammar = grammar
        feature_types = feature_types if feature_types else DEFAULT_FEATURE_TYPES
        self.features = self.construct_features(feature_types)

    def construct_features(self, feature_types: List[Type[Feature]]) -> List[Feature]:
        factory = FeatureFactory(self.grammar)
        return factory.build(feature_types)

    @abstractmethod
    def collect_features(self, test_input: FandangoInput) -> Dict[str, Any]:
        pass


class GrammarFeatureCollector(FeatureCollector):
    def collect_features(self, test_input: FandangoInput) -> FeatureVector:
        feature_vector = FeatureVector(str(test_input))

        for feature in self.features:
            feature_vector.set_feature(feature, feature.default_value)

        self.set_features(test_input.tree, feature_vector)
        return feature_vector

    def set_features(self, tree: DerivationTree, feature_vector: FeatureVector):
        node: Symbol = tree.symbol
        children = tree.children
        assert isinstance(node, NonTerminal)

        corresponding_features_1d = self.get_corresponding_feature(node)

        for corresponding_feature in corresponding_features_1d:
            value = corresponding_feature.evaluate(tree)
            feature_vector.set_feature(corresponding_feature, value)

        for child in children:
            if isinstance(child.symbol, NonTerminal):
                self.set_features(child, feature_vector)

    @lru_cache
    def get_corresponding_feature(self, current_node: NonTerminal) -> List[Feature]:
        return [
            feature
            for feature in self.features
            if (feature.non_terminal == current_node)
        ]
