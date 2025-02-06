from typing import List, Set, Dict, Optional, Any
import re
from abc import ABC, abstractmethod
from collections import defaultdict

from isla.language import DerivationTree
from debugging_framework.input.oracle import OracleResult
from debugging_framework.fuzzingbook.grammar import (
    is_nonterminal,
    reachable_nonterminals,
)

from fandango.language.grammar import Grammar, NonTerminalNode, TerminalNode, Terminal, NonTerminal
from fandangoLearner.reduction.transformer import CleanNameVisitor, DerivableCharsetVisitor, NonTerminalVisitor


class Feature(ABC):
    def __init__(self, non_terminal: NonTerminal):
        self.non_terminal = non_terminal

    def __repr__(self) -> str:
        return (
            self._repr()
            .replace('"', "&quot;")
            .replace(",", "&comma;")
            .replace("[", "&lsqb;")
            .replace("]", "&rsqb;")
            .replace("{", "&lcub;")
            .replace("}", "&rcub;")
            .replace(":", "&colon;")
            .replace("'", "&#39;")
            .replace(" ", "&nbsp;")
            .replace("\n", "&#13;")
            # .replace("\r", "&#60;")
            .replace("\\", "")
        )

    @abstractmethod
    def _repr(self) -> str:
        raise NotImplementedError

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.__hash__() == hash(other)
        return False

    @abstractmethod
    def default_value(self):
        raise NotImplementedError

    @abstractmethod
    def type(self):
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, subtree: DerivationTree) -> Any:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def factory_method(cls, grammar):
        raise NotImplementedError


class ExistenceFeature(Feature):
    def __init__(self, non_terminal: NonTerminal):
        super().__init__(non_terminal)

    def _repr(self) -> str:
        return f"exists({self.non_terminal})"

    @property
    def default_value(self):
        return 0

    @property
    def type(self):
        return int

    def evaluate(self, subtree: DerivationTree) -> int:
        current_node, _ = subtree
        return int(self.non_terminal == current_node)

    @classmethod
    def factory_method(cls, grammar) -> List[Feature]:
        return [cls(non_terminal) for non_terminal in grammar]


class DerivationFeature(Feature):
    def __init__(self, non_terminal: NonTerminal, expansion: NonTerminal | Terminal):
        super().__init__(non_terminal)
        self.expansion = expansion

    def _repr(self) -> str:
        return f"exists({self.non_terminal} -> {self.expansion})"

    @property
    def default_value(self):
        return 0

    @property
    def type(self):
        return int

    def evaluate(self, subtree: DerivationTree) -> int:
        current_node, children = subtree

        expansion = "".join([child[0] for child in children])
        return int(self.non_terminal == current_node and self.expansion == expansion)

    @classmethod
    def factory_method(cls, grammar: Grammar) -> List[Feature]:
        features = []
        clean_name_visitor = CleanNameVisitor()

        for non_terminal in grammar:
            node = grammar.rules[non_terminal]
            if isinstance(node, NonTerminalNode):
                features.append(cls(non_terminal, node.symbol))
            elif isinstance(node, TerminalNode):
                features.append(cls(non_terminal, node.symbol))
            else:
                for expansion in grammar.rules[non_terminal].descendents(grammar.rules):
                    features.append(cls(non_terminal, expansion.symbol))

        return features


class NumericFeature(Feature):
    def _repr(self):
        return f"num({self.non_terminal})"

    @property
    def default_value(self):
        return float("-inf")

    @property
    def type(self):
        return float

    def evaluate(self, subtree: DerivationTree) -> Any:
        try:
            value = float(tree_to_string(subtree))
            return value
        except ValueError:
            return self.default_value

    @classmethod
    def factory_method(cls, grammar) -> List[Feature]:
        v = DerivableCharsetVisitor()
        derivable_chars: dict[NonTerminal, set[str]] = dict()
        for non_terminal in grammar:
            node = grammar.rules[non_terminal]
            derivable_chars[non_terminal] = v.visit(node)

        return cls.get_features(grammar, derivable_chars)

    @classmethod
    def is_numeric(cls, non_terminal: NonTerminal, derivable_chars: dict[NonTerminal, set[str]]) -> bool:
        numeric_chars = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}
        numeric_symbols = {".", "-"}

        chars = derivable_chars[non_terminal]
        non_numeric_chars = (chars - numeric_chars) - numeric_symbols
        has_numeric_chars = len(chars.intersection(numeric_chars)) > 0
        print(chars)
        if len(non_numeric_chars) == 0 and has_numeric_chars:
            return True
        return False

    @classmethod
    def get_features(cls, grammar: Grammar, derivable_chars: Dict[NonTerminal, Set[str]]) -> List[Feature]:
        """
        Gets a list of NumericInterpretation features for each rule that derives only numeric characters.

        :return: A list of NumericInterpretation features.
        """
        features = []
        numeric_chars = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}
        numeric_symbols = {".", "-"}

        non_term_visitor = NonTerminalVisitor()

        for non_terminal in grammar:
            children = non_term_visitor.visit(grammar.rules[non_terminal])
            print(non_terminal, children)

            if all(cls.is_numeric(non_terminal, derivable_chars) for non_terminal in children):
                features.append(cls(non_terminal))

        return features


class LengthFeature(Feature):
    def _repr(self):
        return f"len({self.non_terminal})"

    @property
    def default_value(self):
        return 0

    def type(self):
        return int

    def evaluate(self, subtree: DerivationTree) -> Any:
        return len(tree_to_string(subtree))

    @classmethod
    def factory_method(cls, grammar) -> List[Feature]:
        features = []
        for non_terminal in grammar:
            features.append(cls(non_terminal))
        return features


class FeatureFactory:
    def __init__(self, grammar):
        self.grammar = grammar

    def build(self, feature_types=None) -> List[Feature]:
        if feature_types is None:
            feature_types = [
                ExistenceFeature,
                DerivationFeature,
                NumericFeature,
                LengthFeature,
            ]

        all_features = list()
        for feature_type in feature_types:
            all_features.extend(feature_type.factory_method(self.grammar))
        return all_features


class FeatureVector:
    def __init__(
        self,
        test_input: str,
        result: Optional[OracleResult] = None,
    ):
        self.test_input = test_input
        self.result = result
        self.features: Dict[Feature, Any] = dict()

    def get_feature_value(self, feature: Feature) -> Any:
        if feature in self.features:
            return self.features[feature]
        else:
            return feature.default_value

    def set_feature(self, feature: Feature, value: any):
        if feature in self.features.keys():
            self.features[feature] = max(value, self.features[feature])
        else:
            self.features[feature] = value

    def get_features(self) -> Dict[Feature, Any]:
        return self.features

    def __repr__(self):
        return f"{self.test_input}: {self.features}"


def tree_to_string(tree: DerivationTree) -> str:
    symbol, children, *_ = tree
    if children:
        return "".join(tree_to_string(c) for c in children)
    else:
        return "" if is_nonterminal(symbol) else symbol
