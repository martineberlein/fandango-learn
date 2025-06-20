import logging
import tempfile
import os

from fandango.constraints.base import Constraint
from fandango.language.parse import (
    parse as fandango_parse,
    Grammar,
)


def parse(
    file_path, disable_logging=True, use_cache=True,use_stdlib=False, **kwargs
) -> tuple[Grammar | None, list[Constraint]]:
    """
    Wrapper for the parse function from fandango.language.parse
    """
    if disable_logging:
        logging.getLogger("fandango").disabled = True
    file = open(file_path, "r")
    grammar, constraints = fandango_parse(
        file, use_stdlib=use_stdlib, use_cache=use_cache, **kwargs
    )
    assert isinstance(constraints, list), "Expected a list of constraints"
    assert all(
        isinstance(constraint, Constraint) for constraint in constraints
    ), "Expected a list of constraints"
    return grammar, constraints


def parse_file(
    *args, disable_logging=True, **kwargs
) -> tuple[Grammar | None, list[Constraint]]:
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
    _, constraints = parse_contents(constraint, disable_logging=disable_logging)

    assert len(constraints) == 1, "Expected exactly one constraint"
    assert isinstance(constraints[0], Constraint), "Expected a constraint"
    return constraints[0]


def parse_contents(
    content: str, *args, disable_logging=True, use_stdlib=False, **kwargs
) -> tuple[Grammar | None, list[Constraint]]:
    """
    Wrapper for the parse_contents function from fandango.language.parse
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(content.encode("utf-8"))
        tmp_file_path = tmp_file.name

    try:
        grammar, constraints = parse(
            tmp_file_path, disable_logging=disable_logging,use_stdlib=use_stdlib, **kwargs
        )
    finally:
        os.remove(tmp_file_path)

    return grammar, constraints
