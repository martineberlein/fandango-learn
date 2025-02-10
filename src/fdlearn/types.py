from typing import Callable, Union, Dict

from fdlearn.data import FandangoInput, OracleResult

OracleType = Callable[[Union[FandangoInput, str]], OracleResult]
BatchOracleType = Callable[[Union[set[FandangoInput], set[str]]], Dict[str, OracleResult]]
