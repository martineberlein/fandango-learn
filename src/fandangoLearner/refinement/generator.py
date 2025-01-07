from abc import ABC, abstractmethod
from queue import Queue, Empty
from typing import Set, Union, List

from fandangoLearner.data.input import FandangoInput
from fandangoLearner.learning.candidate import FandangoConstraintCandidate
from fandango.language.grammar import Grammar


class Generator(ABC):
    """
    A generator is responsible for generating inputs to be used in the debugging process.
    """

    def __init__(self, grammar: Grammar, **kwargs):
        """
        Initialize the generator with a grammar.
        """
        self.grammar = grammar

    @abstractmethod
    def generate(self, *args, **kwargs) -> FandangoInput:
        """
        Generate an input to be used in the debugging process.
        """
        raise NotImplementedError

    def generate_test_inputs(self, num_inputs: int = 2, **kwargs) -> Set[FandangoInput]:
        """
        Generate multiple inputs to be used in the debugging process.
        """
        test_inputs = set()
        for _ in range(num_inputs):
            inp = self.generate(**kwargs)
            if inp:
                test_inputs.add(inp)
        return test_inputs

    def run_with_engine(self, candidate_queue: Queue[FandangoConstraintCandidate], output_queue: Union[Queue, List]):
        """
        Run the generator within an engine. This is useful for parallelizing the generation process.
        :param candidate_queue:
        :param output_queue:
        :return:
        """
        try:
            while True:
                test_inputs = self.generate_test_inputs(num_inputs=2, candidate=candidate_queue.get_nowait())
                if isinstance(output_queue, Queue):
                    output_queue.put(test_inputs)
                else:
                    output_queue.append(test_inputs)
        except Empty:
            pass

    def reset(self, **kwargs):
        """
        Reset the generator.
        """
        pass


class FandangoGenerator(Generator):
    """
    The Fandango generator.
    """

    def __init__(self, grammar, **kwargs):
        super().__init__(grammar, **kwargs)

    def generate(self, *args, **kwargs) -> FandangoInput:
        tree = self.grammar.fuzz()

        return FandangoInput(tree)