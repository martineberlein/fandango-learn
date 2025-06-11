from functools import lru_cache
from typing import List, Optional, Type
from abc import ABC, abstractmethod

from fandango.language.grammar import Grammar
from fandango.language.symbol import NonTerminal, Symbol
from fandango.language.tree import DerivationTree

from fdlearn.data import FandangoInput
from fdlearn.reduction.feature_class import (
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
    """
    An abstract class for a feature collector.
    """

    def __init__(
        self, grammar: Grammar, feature_types: Optional[List[Type[Feature]]] = None, filter_features=False
    ):
        """
        Initializes the feature collector with a grammar and optional feature types.
        :param grammar:
        :param feature_types:
        """
        self.grammar = grammar
        feature_types = feature_types if feature_types else DEFAULT_FEATURE_TYPES
        self.features = self.construct_features(feature_types)

        if filter_features:
            self.features = [f for f in self.features if f.non_terminal not in [NonTerminal("<digit>")]]

    def construct_features(self, feature_types: List[Type[Feature]]) -> List[Feature]:
        """
        Constructs the features based on the given feature types.
        :param feature_types: The feature types to construct the features from.
        :return: A list of features.
        """
        factory = FeatureFactory(self.grammar)
        return factory.build(feature_types)

    @abstractmethod
    def collect_features(self, test_input: FandangoInput) -> FeatureVector:
        """
        Collects features for a given input.
        :param test_input: The input for which to collect features.
        :return: A Feature Vector - dictionary of features and their values.
        """
        raise NotImplementedError()


class GrammarFeatureCollector(FeatureCollector):
    """
    A feature collector that collects features based on the grammar of the Fandango language.
    """

    def collect_features(self, test_input: FandangoInput) -> FeatureVector:
        """
        Collects features for a given input.
        :param test_input: The input for which to collect features.
        :return: A Feature Vector - dictionary of features and their values.
        """
        feature_vector = FeatureVector()

        for feature in self.features:
            feature_vector.set_feature(feature, feature.default_value)

        self.set_features(test_input.tree, feature_vector)
        return feature_vector

    def set_features(self, tree: DerivationTree, feature_vector: FeatureVector):
        """
        Sets the features for a given tree.
        :param tree: The tree for which to set the features.
        :param feature_vector: The feature vector to set the features in.
        :return: None
        """
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
        """
        Returns the features that are relevant to the current node.
        :param current_node: The current node for which to get the features.
        :return: A list of features that are relevant to the current node.
        """
        return [
            feature
            for feature in self.features
            if (feature.non_terminal == current_node)
        ]
