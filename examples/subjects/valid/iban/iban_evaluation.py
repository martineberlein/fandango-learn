import random
import sys
import os
import xml.etree.ElementTree as ET
from typing import Callable, Union
from pathlib import Path

from fandango.evolution.algorithm import Fandango
from fandango.language import DerivationTree
from fandango.language.parse import parse, Grammar

from fdlearn.data import OracleResult
from fdlearn.learner import FandangoLearner, FandangoInput, NonTerminal


def validate_iban(iban: str) -> bool:
    """
    Very simple IBAN validity check:
      - No per-country length verification.
    """
    rotated = iban[4:] + iban[:4]
    num_str = "".join(str(int(ch, 36)) for ch in rotated)
    try:
        return int(num_str) % 97 == 1
    except ValueError:
        return False


def oracle(iban: str | FandangoInput) -> OracleResult:
    """
    Oracle function to validate IBANs.
    """
    if isinstance(iban, FandangoInput) or isinstance(iban, DerivationTree):
        iban = str(iban)
    return OracleResult.FAILING if validate_iban(iban) else OracleResult.PASSING


def get_iban_subject() -> tuple[
    Grammar,
    list[FandangoInput],
    Callable[[str | FandangoInput], OracleResult],
    dict,
]:
    base_dir = Path(__file__).parent
    with open(base_dir / "iban.fan", "r") as file:
        grammar, _ = parse(file, use_cache=False, use_stdlib=False)

    initial_inputs = []
    additional_param = {"name": "IBAN"}

    return grammar, initial_inputs, oracle, additional_param
