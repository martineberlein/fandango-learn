import toml
from abc import ABC, abstractmethod
from typing import Dict, List, Set, Iterable, cast, Any

from fandango.constraints.base import Constraint


class PatternRepository(ABC):

    @classmethod
    @abstractmethod
    def from_file(cls, file_path: str = None) -> "PatternRepository":
        """
        Create a pattern repository from a toml file.
        :param str file_path: The path to the toml file.
        :return PatternRepository: The pattern repository.
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def from_data(cls, data: Dict[str, List[Dict[str, str]]]) -> "PatternRepository":
        """
        Create a pattern repository from a dictionary.
        :param Dict[str, List[Dict[str, str]]] data: The dictionary containing the patterns.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_all(self, but: Iterable[str] = tuple()) -> Set[Any]:
        """
        Get all patterns except for the ones in the "but-list".
        :param Iterable[str] but: The list of patterns to exclude.
        :return Set[Any]: The set of patterns.
        """
        raise NotImplementedError()


class FandangoPatternRepository:
    """
    A pattern repository contains a set of patterns that can be used to learn new candidates.
    """

    def __init__(self, data: Dict[str, List[Dict[str, str]]]):
        """
        Create a pattern repository from a dictionary.
        :param Dict[str, List[Dict[str, str]]] data: The dictionary containing the patterns.
        """
        self.groups: Dict[str, Dict[str, language.Formula]] = {
            group_name: {
                entry["name"]: parse_abstract_isla(entry["constraint"])
                for entry in elements
            }
            for group_name, elements in data.items()
        }

    @classmethod
    def from_file(cls, file_path: str = None) -> "FandangoPatternRepository":
        """
        Create a pattern repository from a toml file.
        :param str file_path: The path to the toml file.
        :return PatternRepository: The pattern repository.
        """
        file_name = file_path if file_path else get_pattern_file_path()
        try:
            with open(file_name, "r") as f:
                contents = f.read()
        except FileNotFoundError:
            return cls(dict())

        data: Dict[str, List[Dict[str, str]]] = cast(
            Dict[str, List[Dict[str, str]]], toml.loads(contents)
        )
        return cls(data)

    @classmethod
    def from_data(
        cls, data: Dict[str, List[Dict[str, str]]]
    ) -> "FandangoPatternRepository":
        """
        Create a pattern repository from a dictionary.
        :param Dict[str, List[Dict[str, str]]] data: The dictionary containing the patterns.
        """
        return cls(data)

    def get_all(self, but: Iterable[str] = tuple()) -> Set[Constraint]:
        """
        Get all patterns except for the ones in the "but-list".
        :param Iterable[str] but: The list of patterns to exclude.
        :return Set[Constraint]: The set of patterns.
        """
        exclude = {formula for pattern in but for formula in self[pattern]}
        all_patterns = {
            formula for group in self.groups.values() for formula in group.values()
        }
        return all_patterns - exclude

    def __getitem__(self, item: str) -> Set[Constraint]:
        """
        Get the pattern for a given query.
        """
        for group in self.groups.values():
            if item in group:
                return {group[item]}
        return set()

    def __contains__(self, item: str) -> bool:
        return any(item in group for group in self.groups.values())

    def __len__(self) -> int:
        return sum(len(group) for group in self.groups.values())

    def __str__(self) -> str:
        result = []
        for group, patterns in self.groups.items():
            for name, constraint in patterns.items():
                unparsed_constraint = str(constraint)
                result.append(
                    f"[[{group}]]\n\nname = \"{name}\"\nconstraint = '''\n{unparsed_constraint}\n'''\n"
                )
        return "\n".join(result).strip()
