from typing import Callable, Union

from fdlearn.data import FandangoInput, OracleResult

OracleType = Callable[[Union[FandangoInput, str]], OracleResult]
