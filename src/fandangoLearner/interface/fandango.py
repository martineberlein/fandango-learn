import logging

from fandango.language.parse import parse as fandango_parse, parse_content as fandango_parse_content
from fandango.constraints.base import Constraint


def parse(file_path, disable_logging=True, **kwargs):
    """
    Wrapper for the parse function from fandango.language.parse
    """
    if disable_logging:
        logging.getLogger("fandango").disabled = True
    file = open(file_path, "r")
    return fandango_parse(file, use_stdlib=False, **kwargs)


def parse_file(*args, disable_logging=True, **kwargs):
    """
    Wrapper for the parse_file function from fandango.language.parse
    """
    if disable_logging:
        logging.getLogger("fandango").disabled = True
    return parse(*args, disable_logging=disable_logging, **kwargs)


def parse_constraint(constraint: str, disable_logging=True) -> Constraint:
    """
    Returns a constraint from a constraint string.
    """
    if disable_logging:
        logging.getLogger("fandango").disabled = True
    _, constraints = fandango_parse_content(constraint, use_cache=True)
    assert len(constraints) == 1, "Expected exactly one constraint"
    assert isinstance(constraints[0], Constraint), "Expected a constraint"
    return constraints[0]


def parse_contents(*args, disable_logging=True, **kwargs):
    """
    Wrapper for the parse_contents function from fandango.language.parse
    """
    logging.warning("parse_contents is deprecated, use parse instead")
    if disable_logging:
        logging.getLogger("fandango").disabled = True
    return fandango_parse_content(*args, **kwargs)