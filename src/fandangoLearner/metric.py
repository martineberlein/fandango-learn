"""
This is a copy of the ranking metrics from the Avicenna Tool.
"""

from abc import ABC, abstractmethod

from .candidate import ConstraintCandidate


class FitnessStrategy(ABC):
    """
    Fitness strategy is responsible for evaluating and comparing candidates based on a specific fitness metric.
    """

    @abstractmethod
    def evaluate(self, candidate: ConstraintCandidate):
        """
        Evaluate the candidate based on the specific fitness metric.
        :param candidate: The candidate to evaluate
        """
        raise NotImplementedError("Subclasses should implement this method")

    @abstractmethod
    def compare(self, candidate1: ConstraintCandidate, candidate2: ConstraintCandidate):
        """
        Compare two candidates based on the specific fitness
        :param candidate1: The first candidate
        :param candidate2: The second candidate
        """
        raise NotImplementedError("Subclasses should implement this method")

    def is_equal(
        self, candidate1: ConstraintCandidate, candidate2: ConstraintCandidate
    ):
        """
        Return whether two fitness strategies are equal.
        """
        return self.evaluate(candidate1) == self.evaluate(candidate2)


class PrecisionFitness(FitnessStrategy):
    """
    Precision fitness strategy evaluates and compares candidates based on precision.
    """

    def evaluate(self, candidate: ConstraintCandidate):
        return candidate.precision()

    def compare(self, candidate1: ConstraintCandidate, candidate2: ConstraintCandidate):
        return self.evaluate(candidate1) - self.evaluate(candidate2)


class RecallFitness(FitnessStrategy):
    """
    Recall fitness strategy evaluates and compares candidates based on recall.
    """

    def evaluate(self, candidate: ConstraintCandidate):
        return candidate.recall()

    def compare(self, candidate1: ConstraintCandidate, candidate2: ConstraintCandidate):
        return self.evaluate(candidate1) - self.evaluate(candidate2)


class RecallPriorityFitness(FitnessStrategy):
    """
    Recall priority fitness strategy evaluates and compares candidates based on recall and precision.
    It ranks candidates based on recall first, then precision.
    """

    def evaluate(self, candidate: ConstraintCandidate):
        return candidate.recall(), candidate.precision()

    def compare(self, candidate1: ConstraintCandidate, candidate2: ConstraintCandidate):
        recall1, precision1 = self.evaluate(candidate1)
        recall2, precision2 = self.evaluate(candidate2)
        if recall1 != recall2:
            return recall1 - recall2
        if precision1 != precision2:
            return precision1 - precision2


class RecallPriorityLengthFitness(FitnessStrategy):
    """
    Recall priority fitness strategy evaluates and compares candidates based on recall and precision.
    It ranks candidates based on recall first, then precision, and finally by the length of the formula.
    """

    def evaluate(self, candidate: ConstraintCandidate):
        return candidate.recall(), candidate.precision(), -len(candidate.constraint)

    def compare(self, candidate1: ConstraintCandidate, candidate2: ConstraintCandidate):
        recall1, precision1, length1 = self.evaluate(candidate1)
        recall2, precision2, length2 = self.evaluate(candidate2)
        if recall1 != recall2:
            return recall1 - recall2
        if precision1 != precision2:
            return precision1 - precision2
        return length1 - length2


class F1ScoreFitness(FitnessStrategy):
    """
    F1 score fitness strategy evaluates and compares candidates based on F1 score.
    """

    def evaluate(self, candidate: ConstraintCandidate):
        return (
            2
            * (candidate.precision() * candidate.recall())
            / (candidate.precision() + candidate.recall())
        ), -len(candidate.constraint)

    def compare(self, candidate1: ConstraintCandidate, candidate2: ConstraintCandidate):
        f1_score1, length1 = self.evaluate(candidate1)
        f1_score2, length2 = self.evaluate(candidate2)
        if f1_score1 != f1_score2:
            return f1_score1 - f1_score2
        return length1 - length2


class RecallPriorityStringLengthFitness(RecallPriorityLengthFitness):
    """
    Recall priority fitness strategy evaluates and compares candidates based on recall and precision.
    It ranks candidates based on recall first, then precision, and finally by the string length of the formula.
    """

    def evaluate(self, candidate: ConstraintCandidate):
        return (
            candidate.recall(),
            candidate.precision(),
            -len(str(candidate.constraint)),
        )


class RecallSpecificityLengthFitness(RecallPriorityLengthFitness):
    """
    Recall priority fitness strategy evaluates and compares candidates based on recall and precision.
    It ranks candidates based on recall first, then precision, and finally by the string length of the formula.
    """

    def evaluate(self, candidate: ConstraintCandidate):
        return candidate.recall(), candidate.specificity(), -len(candidate.constraint)


class RecallSpecificityStringLengthFitness(RecallPriorityLengthFitness):
    """
    Recall priority fitness strategy evaluates and compares candidates based on recall and precision.
    It ranks candidates based on recall first, then precision, and finally by the string length of the formula.
    """

    def evaluate(self, candidate: ConstraintCandidate):
        return (
            candidate.recall(),
            candidate.specificity(),
            -len(str(candidate.constraint)),
        )
