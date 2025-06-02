from typing import Callable, Union

from fdlearn.data import FandangoInput, OracleResult

OracleType = Callable[[Union[FandangoInput, str]], OracleResult]
BatchOracleType = Callable[
    [Union[set[FandangoInput], set[str]]], dict[FandangoInput, OracleResult]
]
