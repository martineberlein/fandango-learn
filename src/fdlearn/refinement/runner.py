from abc import ABC, abstractmethod
from typing import Union, Set

from fdlearn.data import FandangoInput, OracleResult
from fdlearn.types import OracleType, BatchOracleType


class ExecutionHandler(ABC):
    def __init__(
        self,
        oracle: OracleType | BatchOracleType,
    ):
        self.oracle: Union[OracleType, BatchOracleType] = oracle

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


class BatchExecutionHandler(ExecutionHandler):
    def _get_label(self, test_inputs: Set[FandangoInput]) -> list[tuple[FandangoInput, OracleResult]]:
        results = self.oracle(test_inputs)

        return [
            (inp, results[inp]) for inp in test_inputs
        ]

    def label(self, test_inputs: Set[FandangoInput], **kwargs):
        test_results = self._get_label(test_inputs)

        for inp, test_result in test_results:
            inp.oracle = test_result
        return test_inputs