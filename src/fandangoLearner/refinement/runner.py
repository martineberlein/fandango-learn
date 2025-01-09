from abc import ABC, abstractmethod
from typing import Callable, Union, Sequence, Optional, Set, List, Tuple

from debugging_framework.input.oracle import OracleResult

from fandangoLearner.data.input import FandangoInput
from fandangoLearner.types import OracleType


class ExecutionHandler(ABC):
    def __init__(
        self,
        oracle: OracleType,
    ):
        self.oracle = oracle

    @abstractmethod
    def label(self, **kwargs):
        raise NotImplementedError


class SingleExecutionHandler(ExecutionHandler):
    def _get_label(self, test_input: Union[FandangoInput]) -> OracleResult:
        return self.oracle(test_input)

    def label(self, test_inputs: Set[FandangoInput], **kwargs):
        for inp in test_inputs:
            label = self._get_label(inp)
            inp.oracle = label
        return test_inputs
