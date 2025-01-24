from typing import Callable, Tuple, Union, Optional
from debugging_framework.input.oracle import OracleResult

from fandangoLearner.data.input import FandangoInput

OracleType = Callable[[Union[FandangoInput, str]], OracleResult]