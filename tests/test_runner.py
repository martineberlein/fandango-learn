import unittest
import os

from fdlearn.data import FandangoInput, OracleResult
from fdlearn.refinement.runner import ExecutionHandler, SingleExecutionHandler, BatchExecutionHandler
from fdlearn.interface import parse


class TestExecutionRunner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, "resources", "calculator.fan")
        cls.grammar, _ = parse(filename)

    def test_single_runner(self):
        def oracle(inp_: FandangoInput) -> OracleResult:
            return OracleResult.FAILING

        inp_1 = FandangoInput.from_str(self.grammar, "sqrt(-1)")
        inp_2 = FandangoInput.from_str(self.grammar, "cos(10)")

        test_inputs = {inp_1, inp_2}

        runner = SingleExecutionHandler(oracle=oracle)
        _ = runner.label(test_inputs)
        for inp in test_inputs:
            self.assertEqual(inp.oracle, OracleResult.FAILING)


    def test_batch_runner(self):
        def oracle(inp_: set[FandangoInput]) -> dict[FandangoInput, OracleResult]:
            result = dict()
            for ip in inp_:
                result[ip] = OracleResult.FAILING
            return result

        inp_1 = FandangoInput.from_str(self.grammar, "sqrt(-1)")
        inp_2 = FandangoInput.from_str(self.grammar, "cos(10)")

        test_inputs = {inp_1, inp_2}

        runner = BatchExecutionHandler(oracle=oracle)
        _ = runner.label(test_inputs)
        for inp in test_inputs:
            self.assertEqual(inp.oracle, OracleResult.FAILING)


if __name__ == '__main__':
    unittest.main()
