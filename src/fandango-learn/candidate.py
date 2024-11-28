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
