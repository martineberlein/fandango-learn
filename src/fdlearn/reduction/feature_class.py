from typing import List, Set, Dict, Any
from abc import ABC, abstractmethod

from fandango.language.tree import DerivationTree
from fandango.language.grammar import (
    Grammar,
    NonTerminalNode,
    TerminalNode,
    Node,
    NonTerminal,
    Alternative,
)

from fdlearn.reduction.transformer import (
    DerivableCharsetVisitor,
    NonTerminalVisitor,
    ExpansionVisitor,
)


class Feature(ABC):
    """
    A feature is a property of a test input that can be used to learn a candidate.
    """

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
    def factory_method(cls, grammar) -> List["Feature"]:
        raise NotImplementedError


class ExistenceFeature(Feature):
    """
    A feature that describes if a non-terminal exists in a given subtree.
    """

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
        return int(self.non_terminal == subtree.symbol)

    @classmethod
    def factory_method(cls, grammar) -> List["ExistenceFeature"]:
        return [cls(non_terminal) for non_terminal in grammar]


class DerivationFeature(Feature):
    """
    A feature that describes if a derivation for a given non-terminal and expansion exists in a subtree.
    """

    def __init__(self, non_terminal: NonTerminal, expansion: Node, grammar: Grammar):
        super().__init__(non_terminal)
        self.expansion = expansion
        self.grammar = grammar

    def _repr(self) -> str:
        return f"exists({self.non_terminal} -> {self.expansion})"

    @property
    def default_value(self):
        return 0

    @property
    def type(self):
        return int

    def evaluate(self, subtree: DerivationTree) -> int:
        """
        With the given fandango Grammar, evaluating this feature is pretty expensive.
        We use a couple of checks to speed up the process. If no checks are passed, we parse the subtree with the
        expansion of the non-terminal and check if the parsed tree exists.

        :param subtree:
        :return:
        """
        current_node = subtree.symbol

        # If the non-terminals don't match, we can immediately return 0
        if self.non_terminal != current_node:
            return 0

        # If the production rule for the non-terminal is not an alternative, we can immediately return 1
        # This is because the expansion of the non-terminal is a single node and it allways has to match the subtree
        if not isinstance(self.grammar[self.non_terminal], Alternative):
            return 1

        # If the expansion of the non-terminal is a terminal or non-terminal, we can compare the subtree with the
        # expansion; ff they match, we can return 1 else 0
        if isinstance(self.expansion, NonTerminalNode) or isinstance(
            self.expansion, TerminalNode
        ):
            # visitor = ExpansionVisitor()
            children = subtree.children
            expanded_subtree = " ".join([repr(child.symbol) for child in children])
            # expanded_expansion = "".join([str(child) for child in visitor.visit(self.expansion)])
            expanded_expansion = repr(self.expansion.symbol)
            if expanded_expansion == expanded_subtree:
                return 1
            return 0

        # If the expansion is an Alternative and consists not of trivial NonTerminal or Terminal nodes, we need to parse
        # the subtree with the expansion of the non-terminal and check if the parsed tree exists.
        new_rules = self.grammar.rules.copy()
        new_rules[self.non_terminal] = self.expansion
        parsed = Grammar.Parser(Grammar(rules=new_rules)).parse(
            str(subtree), start=self.non_terminal
        )
        if parsed:
            return 1

        # visitor = ExpansionVisitor()
        # children = subtree.children
        # expanded_subtree = " ".join([repr(child.symbol) for child in children])
        # expanded_expansion = "".join([str(child) for child in visitor.visit(self.expansion)])
        # print(expanded_subtree, expanded_expansion)
        #
        # return int(self.non_terminal == current_node and expanded_subtree == expanded_expansion)
        return 0

    @classmethod
    def factory_method(cls, grammar: Grammar) -> List["DerivationFeature"]:
        features = []
        visitor = ExpansionVisitor()

        for non_terminal, node in grammar.rules.items():
            for expansion in visitor.visit(node):
                features.append(cls(non_terminal, expansion, grammar))

        return features


class NumericFeature(Feature):
    """
    A feature that describes if all derivable characters for all reachable non-terminals are numeric.
    If so, it returns the numeric value of the subtree.
    """

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
            value = float(str(subtree))
            return value
        except ValueError:
            return self.default_value

    @classmethod
    def factory_method(cls, grammar) -> List["NumericFeature"]:
        """
        Get all derivable chars for all non-terminals in the grammar.
        Get all non-terminals that are reachable for a given non-terminal.

        Check if for a non-terminal all derivable chars for all reachable non-terminals are numeric.

        :param grammar:
        :return:
        """
        features = []
        derivable_char_visitor = DerivableCharsetVisitor()
        derivable_chars: dict[NonTerminal, set[str]] = dict()

        # Get all derivable chars for all non-terminals in the grammar
        for non_terminal, node in grammar.rules.items():
            derivable_chars[non_terminal] = derivable_char_visitor.visit(node)

        # Check if for a non-terminal all derivable chars for all reachable non-terminals are numeric
        for non_terminal, node in grammar.rules.items():
            reachable_non_terminals = get_reachable_non_terminals(grammar, non_terminal)
            reachable_chars = set()
            for reachable_non_terminal in reachable_non_terminals:
                reachable_chars.update(derivable_chars[reachable_non_terminal])
            if cls.is_numeric(reachable_chars):
                features.append(cls(non_terminal))

        return features

    @classmethod
    def is_numeric(cls, char_set: set[str]) -> bool:
        numeric_chars = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}
        numeric_symbols = {".", "-"}

        non_numeric_chars = (char_set - numeric_chars) - numeric_symbols
        has_numeric_chars = len(char_set.intersection(numeric_chars)) > 0
        if len(non_numeric_chars) == 0 and has_numeric_chars:
            return True
        return False


class LengthFeature(Feature):
    """
    A feature that describes the length of the string representation of a given subtree/non-terminal.
    """

    def _repr(self):
        return f"len({self.non_terminal})"

    @property
    def default_value(self):
        return 0

    def type(self):
        return int

    def evaluate(self, subtree: DerivationTree) -> int:
        return len(str(subtree))

    @classmethod
    def factory_method(cls, grammar) -> List["LengthFeature"]:
        features = []
        for non_terminal in grammar:
            features.append(cls(non_terminal))
        return features


class FeatureFactory:
    """
    A factory class to build features for a given grammar.
    """

    def __init__(self, grammar):
        self.grammar = grammar

    def build(self, feature_types=None) -> List[Feature]:
        """
        Build features for a given grammar.

        :param feature_types: The types of features to build.
        :return: A list of features for the grammar.
        """
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
    """
    A feature vector is a set of features that are associated with a test input.
    """

    def __init__(
        self,
    ):
        self.features: Dict[Feature, Any] = dict()

    def get_feature_value(self, feature: Feature) -> Any:
        """
        Get the value of a feature in the feature vector.

        :param feature: The feature to get the value for.
        :return: The value of the feature.
        """
        if feature in self.features:
            return self.features[feature]
        else:
            return feature.default_value

    def set_feature(self, feature: Feature, value: any):
        """
        Set the value of a feature in the feature vector.

        :param feature: The feature to set the value for.
        :param value: The value to set.
        """
        if feature in self.features.keys():
            self.features[feature] = max(value, self.features[feature])
        else:
            self.features[feature] = value

    def get_features(self) -> Dict[Feature, Any]:
        """
        Get all features in the feature vector.

        :return: The features in the feature vector.
        """
        return self.features

    def __repr__(self):
        return f"{self.features}"


def get_reachability_map(grammar: Grammar) -> dict[NonTerminal, Set[NonTerminal]]:
    """
    Get the reachability map for a given grammar.

    :param grammar: The grammar to get the reachability map for.
    :return: The reachability map.s
    """
    reachability_map = dict()
    for non_terminal in grammar.rules:
        reachability_map[non_terminal] = get_reachable_non_terminals(
            grammar, non_terminal
        )

    return reachability_map


def get_reachable_non_terminals(
    grammar: Grammar, non_terminal: NonTerminal
) -> Set[NonTerminal]:
    """
    Get all reachable non-terminals for a given non-terminal in a grammar.

    :param grammar: The grammar to search in.
    :param non_terminal: The non-terminal to search for.
    :return: A set of reachable non-terminals.
    """
    reachable = set()
    non_terminal_visitor = NonTerminalVisitor()

    def _find_reachable_nonterminals(grammar_: Grammar, symbol: NonTerminal):
        nonlocal reachable
        reachable.add(symbol)
        expansion_node = grammar_.rules.get(symbol, [])
        for exp in non_terminal_visitor.visit(expansion_node):
            if exp not in reachable:
                _find_reachable_nonterminals(grammar_, exp)

    _find_reachable_nonterminals(grammar, non_terminal)
    return reachable


def get_direct_reachable_non_terminals(
    grammar: Grammar, non_terminal: NonTerminal
) -> Set[NonTerminal]:
    """
    Get all directly reachable non-terminals for a given non-terminal in a grammar.

    :param grammar: The grammar to search in.
    :param non_terminal: The non-terminal to search for.
    :return: A set of reachable non-terminals.
    """
    reachable = set()
    non_terminal_visitor = NonTerminalVisitor()

    def _find_reachable_nonterminals(grammar_: Grammar, symbol: NonTerminal):
        nonlocal reachable
        expansion_node = grammar_.rules.get(symbol, [])
        for exp in non_terminal_visitor.visit(expansion_node):
            if exp not in reachable:
                reachable.add(exp)

    _find_reachable_nonterminals(grammar, non_terminal)
    return reachable


def get_direct_reachability_map(grammar: Grammar) -> dict[NonTerminal, Set[NonTerminal]]:
    """
    Get the reachability map for a given grammar.

    :param grammar: The grammar to get the reachability map for.
    :return: The reachability map.s
    """
    reachability_map = dict()
    for non_terminal in grammar.rules:
        reachability_map[non_terminal] = get_direct_reachable_non_terminals(
            grammar, non_terminal
        )

    return reachability_map