from dataclasses import dataclass, field

from fandango.language.grammar import Grammar

from fdlearn.data import FandangoInput
from fdlearn.types import OracleType


@dataclass
class Subject:
    name: str = ""
    grammar: Grammar = None
    initial_inputs: set[FandangoInput] = None
    oracle: OracleType = None
    other_parameter: dict = field(default_factory=dict)
