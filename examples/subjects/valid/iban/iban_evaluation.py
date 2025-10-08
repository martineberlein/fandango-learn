import random
import sys
import os
import xml.etree.ElementTree as ET
from typing import Callable, Union
from pathlib import Path

from fandango.evolution.algorithm import Fandango
from fandango.language import DerivationTree
from fandango.language.parse import parse, Grammar

from examples.subjects.subject import Subject
from fdlearn.data import OracleResult
from fdlearn.learner import FandangoLearner, FandangoInput, NonTerminal

from examples.subjects.subject import Subject


def validate_iban(iban: str) -> bool:
    chk = int(iban[2:4])
    if not (2 <= chk <= 97):
        return False

    rotated = iban[4:] + iban[:4]
    numeric = ''.join(str(ord(ch) - 55) if ch.isalpha() else ch for ch in rotated)
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False

def iban_checksum(iban: str) -> int:
    country = iban[:2]
    bban = iban[4:]
    moved = bban + country + "00"
    numeric = ''.join(str(ord(ch) - 55) if ch.isalpha() else ch for ch in moved)
    remainder = int(numeric) % 97
    check_digits = 98 - remainder
    return check_digits



def oracle(iban: str | FandangoInput) -> OracleResult:
    """
    Oracle function to validate IBANs.
    """
    if isinstance(iban, FandangoInput) or isinstance(iban, DerivationTree):
        iban = str(iban)
    return OracleResult.FAILING if validate_iban(iban) else OracleResult.PASSING


def get_iban_subject() -> Subject:
    base_dir = Path(__file__).parent
    with open(base_dir / "iban.fan", "r") as file:
        grammar, _ = parse(file, use_cache=False, use_stdlib=False)

    initial_inputs = []

    return Subject(
        name="IBAN",
        grammar=grammar,
        initial_inputs=initial_inputs,
        oracle=oracle
    )


if __name__ =="__main__":
    # print(validate_iban("DE89370400440532013000"))
    # print(oracle("DE89370400440532013000"))
    # print(iban_checksum("DE89370400440532013000"))
    print(validate_iban("LU0122"))
    print(iban_checksum("LU0122"))


    """
    NL9969
BE016774
LU0122
NL0008
BE002
LU994
ES013
BE0181
GB01888


Remaining Positives (6):
BE002 FAILING
GB01888 FAILING
NL0008 FAILING
LU0122 FAILING
BE0181 FAILING
ES013 FAILING
Remaining Positives (1):
ES013 FAILING

"""