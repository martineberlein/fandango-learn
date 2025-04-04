"""
This is a copy of the Input Class that used within Avicenna.
An Input instance represents a test input comprising a derivation tree and an associated oracle result.
It can also hold features and an index for the derivation tree.
For Fandango, we use the provided Derivation tree implementation.
"""

from abc import ABC, abstractmethod
from typing import Generator, Optional, Final

from fandango.language.tree import DerivationTree
from fandango.language.grammar import Grammar

from fdlearn.data.oracle import OracleResult
from fdlearn.reduction.feature_class import FeatureVector


class Input(ABC):
    """
    Represents a test input comprising a derivation tree and an associated oracle result.
    The derivation tree represents the parsed structure of the input, and the oracle result
    provides the outcome when this input is processed by a system under test.
    """

    def __init__(self, tree: DerivationTree, oracle: OracleResult = None):
        """
        Initializes the Input instance with a derivation tree and an optional oracle result.

        :param DerivationTree tree: The derivation tree of the input.
        :param OracleResult oracle: The optional oracle result associated with the input.
        """
        assert isinstance(
            tree, DerivationTree
        ), f"tree must be an instance of DerivationTree, but is {type(tree)}"
        self.__tree: Final[DerivationTree] = tree
        self.__oracle: Optional[OracleResult] = oracle
        self.__features: Optional[FeatureVector] = None

    @property
    def tree(self) -> DerivationTree:
        """
        Retrieves the derivation tree of the input.
        :return DerivationTree: The derivation tree.
        """
        return self.__tree

    @property
    def oracle(self) -> OracleResult:
        """
        Retrieves the oracle result associated with the input.
        :return OracleResult: The oracle result, or None if not set.
        """
        return self.__oracle

    @property
    def features(self) -> FeatureVector:
        """
        Retrieves the features associated with the input.
        :return: The features associated with the input.
        """
        return self.__features

    @oracle.setter
    def oracle(self, oracle_: OracleResult):
        """
        Sets the oracle result for the input.
        :param OracleResult oracle_: The new oracle result to set.
        """
        self.__oracle = oracle_

    @features.setter
    def features(self, features_: FeatureVector):
        """
        Sets the features for the input.
        :param FeatureVector features_: The new features to set.
        """
        self.__features = features_

    def update_oracle(self, oracle_: OracleResult) -> "Input":
        """
        Updates the oracle result for the input and returns the modified input instance.
        :param OracleResult oracle_: The new oracle result to set.
        :return Input: The current input instance with the updated oracle.
        """
        self.__oracle = oracle_
        return self

    def update_features(self, features_: FeatureVector) -> "Input":
        """
        Updates the features for the input and returns the modified input instance.
        :param FeatureVector features_: The new features to set.
        :return Input: The current input instance with the updated features.
        """
        self.__features = features_
        return self

    def __repr__(self) -> str:
        """
        Provides the canonical string representation of the Input instance.
        :return str: A string representation that can recreate the Input instance.
        """
        return f"Input({repr(self.tree)}, {repr(self.oracle)})"

    def __str__(self) -> str:
        """
        Provides a user-friendly string representation of the Input's derivation tree.
        :return str: The string representation of the derivation tree.
        """
        return str(self.__tree)

    @abstractmethod
    def __hash__(self) -> int:
        """
        Generates a hash based on the structural hash of the derivation tree.
        :return int: The hash value.
        """
        # return self.__tree.structural_hash()
        raise NotImplementedError()

    def __eq__(self, other) -> bool:
        """
        Determines equality based on the structural hash of the derivation trees.
        :param other: The object to compare against.
        :return bool: True if the other object is an Input with an equal derivation tree.
        """
        return isinstance(other, Input) and self.__hash__() == hash(other)

    def __iter__(self) -> Generator[DerivationTree | OracleResult | None, None, None]:
        """
        Allows tuple unpacking of the input, e.g., tree, oracle = input.
        :return Generator[DerivationTree | OracleResult | None, None]: An iterator yielding the tree and oracle.
        """
        yield self.tree
        yield self.oracle

    def __getitem__(self, item: int) -> Optional[DerivationTree] | OracleResult:
        """
        Allows indexed access to the input's derivation tree and oracle.
        :param int item: The index of the item to get (0 for tree, 1 for oracle).
        :return Optional[DerivationTree] | OracleResult: The requested component of the input.
        """
        assert (
            isinstance(item, int) and 0 <= item <= 1
        ), "Index must be 0 (tree) or 1 (oracle)"
        return self.tree if item == 0 else self.oracle

    @classmethod
    def from_str(cls, grammar, input_string, oracle: Optional[OracleResult] = None):
        """
        Factory method to create an Input instance from a string using the specified grammar.
        :param grammar: The grammar used for parsing the input string.
        :param str input_string: The input string to parse.
        :param Optional[OracleResult] oracle: The optional oracle result.
        :return Input: The created Input instance.
        """

        raise NotImplementedError()


class FandangoInput(Input):
    """
    An Input instance representing a test input for the Fandango language.
    """

    def __init__(self, tree: DerivationTree, oracle: Optional[OracleResult] = None):
        super().__init__(tree, oracle)
        self.hash = hash(self.tree)

    def __hash__(self) -> int:
        """
        Generates a hash based on the structural hash of the derivation tree.
        :return:
        """
        return self.hash

    @classmethod
    def from_str(
        cls,
        grammar: Grammar,
        input_string,
        oracle: Optional[OracleResult | bool] = None,
    ):
        """
        Factory method to create an Input instance from a string using the specified grammar.
        :param grammar: The grammar used for parsing the input string.
        :param input_string: The input string to parse.
        :param oracle: The optional oracle result.
        :return: The created Input instance.
        """
        tree = grammar.parse(input_string)
        if isinstance(oracle, bool):
            oracle = OracleResult.FAILING if oracle else OracleResult.PASSING
        if tree:
            return cls(
                grammar.parse(input_string),
                oracle,
            )
        else:
            raise SyntaxError(f"Could not parse input_string '{input_string}'.")
