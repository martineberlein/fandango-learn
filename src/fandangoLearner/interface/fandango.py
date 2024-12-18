from fandango.language.parse import parse as fandango_parse, parse_file as fandango_parse_file
from fandango.constraints.base import Constraint

def parse(*args, **kwargs):
    """
    Wrapper for the parse function from fandango.language.parse
    :param args:
    :param kwargs:
    :return:
    """
    return fandango_parse(*args, **kwargs)


def parse_file(*args, **kwargs):
    """
    Wrapper for the parse_file function from fandango.language.parse
    :param args:
    :param kwargs:
    :return:
    """
    return fandango_parse_file(*args, **kwargs)


def parse_constraint(constraint: str) -> Constraint:
    """
    Returns a constraint from a constraint string.
    :param args:
    :param kwargs:
    :return:
    """
    _, constraints = parse(constraint)
    assert len(constraints) == 1, "Expected exactly one constraint"
    return constraints[0]
