from fandango.language.symbol import NonTerminal
from enum import Enum


class PlaceholderType(Enum):
    NonTerminal = "NonTerminal"
    Int = "int"
    String = "string"


class Placeholder(NonTerminal):
    """
    A placeholder is a symbol that represents a type of value, such as a non-terminal, integer or string.
    """
    def __init__(self, placeholder_type: PlaceholderType):
        if not isinstance(placeholder_type, PlaceholderType):
            raise ValueError(f"Invalid placeholder type: {placeholder_type}")
        self.ph_type = placeholder_type
        super().__init__(f"<pl_{self.ph_type.value}>")

    def __repr__(self):
        return f"Placeholder({self.ph_type.value})"

    def __str__(self):
        return super().__repr__()

    def __eq__(self, other):
        return isinstance(other, Placeholder) and self.ph_type == other.ph_type

    def __hash__(self):
        return hash((self.ph_type, self.type))

    @classmethod
    def non_terminal(cls) -> "Placeholder":
        """
        Create a placeholder for a non-terminal.
        :return: Placeholder: The placeholder for a non-terminal.
        """
        return cls(PlaceholderType.NonTerminal)

    @classmethod
    def int(cls) -> "Placeholder":
        """
        Create a placeholder for an integer.
        :return: Placeholder: The placeholder for an integer.
        """
        return cls(PlaceholderType.Int)

    @classmethod
    def string(cls) -> "Placeholder":
        """
        Create a placeholder for a string.
        :return: Placeholder: The placeholder for a string.
        """
        return cls(PlaceholderType.String)

