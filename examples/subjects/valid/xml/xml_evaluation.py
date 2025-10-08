import random
import sys
import os
import xml.etree.ElementTree as ET
from typing import Callable, Union
from pathlib import Path

from fandango.evolution.algorithm import Fandango
from fandango.language.parse import parse, Grammar

from examples.subjects.subject import Subject
from fdlearn.data import OracleResult
from fdlearn.learner import FandangoLearner, FandangoInput, NonTerminal


def oracle(inp: str | FandangoInput) -> OracleResult:
    """
    Oracle function to validate IBANs.
    """
    try:
        ET.fromstring(str(inp))
    except ET.ParseError:
        return OracleResult.PASSING
    except Exception:
        return OracleResult.UNDEFINED
    return OracleResult.FAILING


def get_xml_subject() -> Subject:
    base_dir = Path(__file__).parent
    with open(base_dir / "xml.fan", "r") as file:
        grammar, _ = parse(file, use_cache=False, use_stdlib=False)

    initial_inputs = []

    return Subject(
        name="XML", grammar=grammar, initial_inputs=initial_inputs, oracle=oracle
    )
