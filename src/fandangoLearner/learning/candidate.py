from typing import Dict, List, Optional
from abc import ABC, abstractmethod

from debugging_framework.input.oracle import OracleResult

from fandango.constraints.base import (
    Constraint,
    ConjunctionConstraint,
    DisjunctionConstraint,
)
from fandangoLearner.data.input import FandangoInput


class ConstraintCandidate(ABC):
    """
    Represents a learned candidate.
    """

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
    """
    Represents a learned candidate constraint of the Fandango learner.
    This class encapsulates a constraint and provides methods for evaluating the constraint fast and efficiently.
    """

    def __init__(
        self,
        constraint: Constraint,
        failing_inputs_eval_results: Optional[List[bool]] = None,
        passing_inputs_eval_results: Optional[List[bool]] = None,
        cache: Optional[Dict[FandangoInput, bool]] = None,
    ):
        super().__init__(constraint)
        self.failing_inputs_eval_results = failing_inputs_eval_results or []
        self.passing_inputs_eval_results = passing_inputs_eval_results or []
        self.cache: Dict[FandangoInput, bool] = cache or {}

    def evaluate(self, inputs):
        """
        Evaluate the fandango constraint on a set of inputs.
        :param inputs:
        :return:
        """
        for inp in inputs:
            eval_result = self.constraint.check(inp.tree)
            self._update_eval_results_and_combination(eval_result, inp)

    def specificity(self) -> float:
        """
        Return the specificity of the candidate.
        """
        if len(self.passing_inputs_eval_results) == 0:
            return 0.0
        return sum(not int(entry) for entry in self.passing_inputs_eval_results) / len(
            self.passing_inputs_eval_results
        )

    def recall(self) -> float:
        """
        Return the recall of the candidate.
        """
        if len(self.failing_inputs_eval_results) == 0:
            return 0.0
        return sum(int(entry) for entry in self.failing_inputs_eval_results) / len(
            self.failing_inputs_eval_results
        )

    def precision(self) -> float:
        """
        Return the precision of the candidate.
        """
        tp = sum(int(entry) for entry in self.failing_inputs_eval_results)
        fp = sum(int(entry) for entry in self.passing_inputs_eval_results)
        return tp / (tp + fp) if tp + fp > 0 else 0.0

    def __and__(
        self, other: "FandangoConstraintCandidate"
    ) -> "FandangoConstraintCandidate":
        """
        Return the conjunction of the candidate with another candidate.

        :param other: The other candidate.
        :return: The conjunction of the candidate with the other candidate.
        """
        assert isinstance(other, FandangoConstraintCandidate)
        assert self.cache.keys() == other.cache.keys()

        new_failing_inputs_eval_results = []
        new_passing_inputs_eval_results = []
        new_cache = {}
        for inp in self.cache:
            r = self.cache[inp] and other.cache[inp]
            if inp.oracle == OracleResult.FAILING:
                new_failing_inputs_eval_results.append(r)
            else:
                new_passing_inputs_eval_results.append(r)
            new_cache[inp] = r

        return FandangoConstraintCandidate(
            constraint=ConjunctionConstraint(
                [self.constraint, other.constraint],
                local_variables=self.constraint.local_variables,
                global_variables=self.constraint.global_variables,
                # lazy=self.constraint.lazy,
            ),
            failing_inputs_eval_results=new_failing_inputs_eval_results,
            passing_inputs_eval_results=new_passing_inputs_eval_results,
            cache=new_cache,
        )

    def __or__(
        self, other: "FandangoConstraintCandidate"
    ) -> "FandangoConstraintCandidate":
        """
        Return the disjunction of the candidate with another candidate.

        :param other: The other candidate.
        :return: The disjunction of the candidate with the other candidate.
        """
        assert isinstance(other, FandangoConstraintCandidate)

        new_failing_inputs_eval_results = []
        new_passing_inputs_eval_results = []
        new_cache = {}
        for inp in self.cache:
            r = self.cache[inp] or other.cache[inp]
            if inp.oracle == OracleResult.FAILING:
                new_failing_inputs_eval_results.append(r)
            else:
                new_passing_inputs_eval_results.append(r)
            new_cache[inp] = r

        return FandangoConstraintCandidate(
            constraint=DisjunctionConstraint(
                [self.constraint, other.constraint],
                local_variables=self.constraint.local_variables,
                global_variables=self.constraint.global_variables,
            ),
            failing_inputs_eval_results=new_failing_inputs_eval_results,
            passing_inputs_eval_results=new_passing_inputs_eval_results,
            cache=new_cache,
        )

    def _update_eval_results_and_combination(
        self, eval_result: bool, inp: FandangoInput
    ):
        """
        Update the evaluation results and combination with a new input and its evaluation result.
        """
        if inp.oracle == OracleResult.FAILING:
            self.failing_inputs_eval_results.append(eval_result)
        else:
            self.passing_inputs_eval_results.append(eval_result)
        self.cache[inp] = eval_result

    def reset(self):
        self.failing_inputs_eval_results = []
        self.passing_inputs_eval_results = []
        self.cache = {}

    def __str__(self):
        return (
            f"{self.constraint}, "
            f"Precision: {self.precision()}, "
            f"Recall: {self.recall()} "
            f"(based on {len(self.failing_inputs_eval_results)} failing "
            f"and {len(self.passing_inputs_eval_results)} passing inputs)"
        )
