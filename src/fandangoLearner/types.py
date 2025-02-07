from typing import Callable, Union

from fandangoLearner.data import FandangoInput, OracleResult

OracleType = Callable[[Union[FandangoInput, str]], OracleResult]
