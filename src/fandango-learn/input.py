from abc import ABC, abstractmethod

from fandango.language.tree import DerivationTree


class TestInput(ABC):

    def __init__(self, tree):
        self.tree = tree


class FandangoInput(TestInput):

    def __init__(self, tree):
        super().__init__(tree)

    @abstractmethod
    def explain(self, *args, **kwargs):
        """
        Explain the input features that result in the failure of a program.
        """
        raise NotImplementedError()