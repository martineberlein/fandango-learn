from typing import Dict, List, Set, Sequence
from abc import ABC, abstractmethod

from fandango.constraints.base import Constraint


class ConstraintCandidate(ABC):

    def __init__(self, constraint):
        self.constraint = constraint

    @abstractmethod
    def evaluate(self, inputs):
        pass

    @abstractmethod
    def precision(self):
        pass

    @abstractmethod
    def recall(self):
        pass

    @abstractmethod
    def specificity(self):
        pass

    @abstractmethod
    def __and__(self, other):
        pass

    @abstractmethod
    def __or__(self, other):
        pass


class FandangoConstraintCandidate(ConstraintCandidate):

    def __init__(self, constraint: Constraint):
        super().__init__(constraint)

    def evaluate(self, inputs):
        pass

    def precision(self):
        pass

    def recall(self):
        pass

    def specificity(self):
        pass

    def __and__(self, other):
        pass

    def __or__(self, other):
        pass

# class Candidate:
#     """
#     A candidate contains a formula, a set of inputs, a list of evaluation results and a combination of inputs and
#     evaluation results.
#     """
#
#     def __init__(
#         self,
#         formula: language.Formula,
#         inputs: Set[Input] = None,
#         positive_eval_results: Sequence[bool] = (),
#         negative_eval_results: Sequence[bool] = (),
#         comb: Dict[Input, bool] = None,
#         use_fast_eval: bool = False,
#         eval_ast: list = None,
#     ):
#         """
#         Initialize a candidate with a formula, a set of inputs, a list of evaluation results and a combination of inputs
#         and evaluation results.
#         :param Formula formula: The formula of the candidate.
#         :param Set[Input] inputs: The inputs of the candidate.
#         :param Sequence[bool] positive_eval_results: The evaluation results of the candidate on positive inputs.
#         :param Sequence[bool] negative_eval_results: The evaluation results of the candidate on negative inputs.
#         :param Dict[Input, bool] comb: The combination of inputs and evaluation results.
#         """
#         self.formula = formula
#         self.inputs = inputs or set()
#         self.failing_inputs_eval_results: List[bool] = list(positive_eval_results)
#         self.passing_inputs_eval_results: List[bool] = list(negative_eval_results)
#         self.comb: Dict[Input, bool] = comb or {}
#         self.use_fast_eval = use_fast_eval
