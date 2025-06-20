import time
from abc import ABC, abstractmethod
from queue import Queue, Empty
from typing import Set, Union, List

from fandango.language.grammar import Grammar
from fandango.evolution.algorithm import Fandango

from fdlearn.logger import LOGGER
from fdlearn.data.input import FandangoInput
from fdlearn.learning.candidate import FandangoConstraintCandidate


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

    def run_with_engine(self, candidate_queue: Queue, output_queue: Union[Queue, List]):
        try:
            while True:
                try:
                    candidate = candidate_queue.get_nowait()
                    LOGGER.debug(f"Got candidate: {candidate}")
                    test_inputs = self.generate_test_inputs(candidate=candidate)
                    output_queue.put(test_inputs)
                except Empty:
                    LOGGER.debug("Candidate queue empty, exiting.")
                    break
        except Exception as e:
            LOGGER.error(f"Exception in run_with_engine: {e}")

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

    def generate_test_inputs(
        self,
        candidate: FandangoConstraintCandidate = None,
        num_inputs: int = 2,
        time_out: int = 1,
        **kwargs,
    ) -> List[FandangoInput]:
        """
        Generate multiple inputs to be used in the debugging process.
        """
        test_inputs_hashes = set()
        test_inputs: list[FandangoInput] = list()
        start_time = time.time()
        while len(test_inputs) < num_inputs and time.time() - start_time < time_out:
            new_inputs = self.generate(candidate=candidate, **kwargs)
            for inp in new_inputs:
                if inp not in test_inputs_hashes:
                    test_inputs_hashes.add(inp)
                    test_inputs.append(inp)
        LOGGER.debug("took: ", time.time() - start_time, candidate, len(test_inputs))
        return test_inputs[:num_inputs]

    def generate(
        self, candidate: FandangoConstraintCandidate = None, **kwargs
    ) -> Set[FandangoInput]:
        fandango = Fandango(
            grammar=self.grammar,
            constraints=[candidate.constraint],
            max_generations=50,
            desired_solutions=2,
            # random_seed=1,
            warnings_are_errors=True,
        )

        solutions = fandango.evolve()
        return {FandangoInput(inp) for inp in solutions}


class FandangoGrammarGenerator(Generator):
    """
    The Fandango grammar generator.
    """

    def __init__(self, grammar, **kwargs):
        super().__init__(grammar, **kwargs)

    def generate(self, **kwargs) -> FandangoInput:
        return FandangoInput(tree=self.grammar.fuzz())

    def generate_test_inputs(
        self,
        candidate: FandangoConstraintCandidate = None,
        num_inputs: int = 5,
        time_out: int = 1,
        **kwargs,
    ) -> Set[FandangoInput]:
        """
        Generate multiple inputs to be used in the debugging process.
        """
        test_inputs: Set[FandangoInput] = set()
        start_time = time.time()
        while len(test_inputs) < num_inputs and time.time() - start_time < time_out:
            new_input = self.generate(candidate=candidate, **kwargs)
            test_inputs.add(new_input)

        return test_inputs
