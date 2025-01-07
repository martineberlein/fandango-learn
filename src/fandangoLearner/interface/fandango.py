import logging

from fandango.language.parse import parse as fandango_parse, parse_file as fandango_parse_file
from fandango.constraints.base import Constraint


def parse(*args, disable_logging=True, **kwargs):
    """
    Wrapper for the parse function from fandango.language.parse
    """
    if disable_logging:
        logging.getLogger("fandango").disabled = True
    return fandango_parse(*args, **kwargs)


def parse_file(*args, disable_logging=True, **kwargs):
    """
    Wrapper for the parse_file function from fandango.language.parse
    """
    if disable_logging:
        logging.getLogger("fandango").disabled = True
    return fandango_parse_file(*args, **kwargs)


def parse_constraint(constraint: str) -> Constraint:
    """
    Returns a constraint from a constraint string.
    """
    _, constraints = parse(constraint)
    assert len(constraints) == 1, "Expected exactly one constraint"
    return constraints[0]
