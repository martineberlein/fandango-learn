from abc import ABC
from enum import Enum


class PlaceholderVariable(Enum):
    NON_TERMINAL_PLACEHOLDER = "NON_TERMINAL_PLACEHOLDER"
    STRING_PLACEHOLDER = "STRING_PLACEHOLDER"
    INTEGER_PLACEHOLDER = "INTEGER_PLACEHOLDER"
    BOOLEAN_PLACEHOLDER = "BOOLEAN_PLACEHOLDER"

    def __str__(self):
        return self.value
