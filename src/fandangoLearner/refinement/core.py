from abc import ABC, abstractmethod
from typing import Iterable, Optional, Set, List, Union
import time
import logging

from fandango.language.grammar import Grammar
from fandango.language.symbol import NonTerminal

from fandangoLearner.types import OracleType
from fandangoLearner.data.input import FandangoInput
from fandangoLearner.core import ConstraintCandidateLearner
from fandangoLearner.learner import FandangoLearner
from fandangoLearner.learning.candidate import FandangoConstraintCandidate
from fandangoLearner.learning.metric import FitnessStrategy, RecallPriorityStringLengthFitness
from fandangoLearner.logger import LoggerLevel, LOGGER
from .generator import Generator, FandangoGrammarGenerator, FandangoGenerator
from .runner import SingleExecutionHandler, ExecutionHandler
from .engine import Engine, SingleEngine, ParallelEngine
from .negation import construct_negations


class InputFeatureDebugger(ABC):
    """
    Interface for debugging input features that result in the failure of a program.
    """

    def __init__(
        self,
        grammar: Grammar,
        oracle: OracleType,
        initial_inputs: Union[Iterable[str], Iterable[FandangoInput]],
        logger_level: LoggerLevel = LoggerLevel.INFO,
    ):
        """
        Initialize the input feature debugger with a grammar, oracle, and initial inputs.
        """
        LOGGER.setLevel(logger_level.value)

        self.initial_inputs = initial_inputs
        self.grammar = grammar
        self.oracle = oracle

    @abstractmethod
    def explain(self, *args, **kwargs):
        """
        Explain the input features that result in the failure of a program.
        """
        raise NotImplementedError()


class HypothesisInputFeatureDebugger(InputFeatureDebugger, ABC):
    """
    A hypothesis-based input feature debugger.
    """

    def __init__(
        self,
        grammar: Grammar,
        oracle: OracleType,
        initial_inputs: Union[Iterable[str], Iterable[FandangoInput]],
        learner: Optional[FandangoLearner] = None,
        generator: Optional[Generator] = None,
        timeout_seconds: int = 3600,
        max_iterations: Optional[int] = 10,
        **kwargs,
    ):
        """
        Initialize the hypothesis-based input feature debugger with a grammar, oracle, initial inputs,
        learner, generator, and runner.
        """
        super().__init__(grammar, oracle, initial_inputs, **kwargs)
        self.timeout_seconds = timeout_seconds
        self.max_iterations = max_iterations
        self.strategy = RecallPriorityStringLengthFitness()
        self.learner: FandangoLearner = (
            learner if learner else FandangoLearner(self.grammar)
        )
        self.generator: Generator = (
            generator if generator else FandangoGrammarGenerator(self.grammar)
        )
        self.runner: ExecutionHandler = SingleExecutionHandler(self.oracle)
        # self.engine: Engine = SingleEngine(generator)

    def set_runner(self, runner: ExecutionHandler):
        """
        Set the runner for the hypothesis-based input feature debugger.
        """
        self.runner = runner

    def set_learner(self, learner: ConstraintCandidateLearner):
        """
        Set the learner for the hypothesis-based input feature debugger.
        """
        self.learner = learner

    def set_generator(self, generator: Generator):
        """
        Set the generator for the hypothesis-based input feature debugger.
        """
        self.generator = generator

    def set_timeout(self) -> Optional[float]:
        """
        Set the timeout for the hypothesis-based input feature debugger.
        Returns the start time if the timeout is set, otherwise None.
        """
        if self.timeout_seconds is not None:
            return int(time.time())
        return None

    def check_timeout_reached(self, start_time) -> bool:
        """
        Check if the timeout has been reached.
        """
        if self.timeout_seconds is None:
            return False
        return time.time() - start_time >= self.timeout_seconds

    def check_iterations_reached(self, iteration) -> bool:
        """
        Check if the maximum number of iterations has been reached.
        """
        return iteration >= self.max_iterations

    def check_iteration_limits(self, iteration, start_time) -> bool:
        """
        Check if the iteration limits have been reached.
        :param iteration: The current iteration.
        :param start_time: The start time of the input feature debugger.
        """
        if self.check_iterations_reached(iteration):
            return False
        if self.check_timeout_reached(start_time):
            return False
        return True

    def explain(self) -> Optional[List[FandangoConstraintCandidate]]:
        """
        Explain the input features that result in the failure of a program.
        """
        iteration = 0
        start_time = self.set_timeout()
        LOGGER.info("Starting the hypothesis-based input feature debugger.")
        try:
            test_inputs: Set[FandangoInput] = self.prepare_test_inputs()

            while self.check_iteration_limits(iteration, start_time):
                LOGGER.info(f"Starting iteration {iteration}.")
                new_test_inputs = self.hypothesis_loop(test_inputs)
                test_inputs.update(new_test_inputs)

                iteration += 1
        except TimeoutError as e:
            logging.error(e)
        except Exception as e:
            logging.error(e)
        finally:
            return self.get_best_candidates()

    def prepare_test_inputs(self) -> Set[FandangoInput]:
        """
        Prepare the input feature debugger.
        """
        test_inputs: Set[FandangoInput] = self.get_test_inputs_from_strings(self.initial_inputs)
        test_inputs = self.run_test_inputs(test_inputs)
        self.check_initial_conditions(test_inputs)
        return test_inputs

    def hypothesis_loop(self, test_inputs: Set[FandangoInput]) -> Set[FandangoInput]:
        """
        The main loop of the hypothesis-based input feature debugger.
        """
        candidates = self.learn_candidates(test_inputs)
        negated_candidates = self.negate_candidates(candidates)
        inputs = self.generate_test_inputs(candidates + negated_candidates)
        labeled_test_inputs = self.run_test_inputs(inputs)
        return labeled_test_inputs

    def learn_candidates(self, test_inputs: Set[FandangoInput]) -> Optional[List[FandangoConstraintCandidate]]:
        """
        Learn the candidates (failure diagnoses) from the test inputs.
        """
        raise NotImplementedError()

    @staticmethod
    def negate_candidates(candidates: List[FandangoConstraintCandidate]):
        """
        Negate the learned candidates.
        """
        negated_candidates = construct_negations(candidates)
        return negated_candidates

    def generate_test_inputs(self, candidates: List[FandangoConstraintCandidate]) -> Set[FandangoInput]:
        """
        Generate the test inputs based on the learned candidates.
        :param candidates: The learned candidates.
        :return Set[Input]: The generated test inputs.
        """
        raise NotImplementedError()

    def run_test_inputs(self, test_inputs: Set[FandangoInput]) -> Set[FandangoInput]:
        """
        Run the test inputs.
        """
        LOGGER.info("Running the test inputs.")
        return self.runner.label(test_inputs=test_inputs)

    def get_best_candidates(
        self, strategy: Optional[FitnessStrategy] = None
    ) -> Optional[List[FandangoConstraintCandidate]]:
        """
        Return the best candidate.
        """
        strategy = strategy if strategy else self.strategy
        candidates = self.learner.get_best_candidates()
        sorted_candidates = sorted(candidates, key=lambda c: strategy.evaluate(c), reverse=True) if candidates else []
        return sorted_candidates

    def get_test_inputs_from_strings(self, inputs: Iterable[str]) -> Set[FandangoInput]:
        """
        Convert a list of input strings to a set of Input objects.
        """
        return set([FandangoInput.from_str(self.grammar, inp, None) for inp in inputs])

    @staticmethod
    def check_initial_conditions(test_inputs: Set[FandangoInput]):
        """
        Check the initial conditions for the input feature debugger.
        Raises a ValueError if the conditions are not met.
        """

        has_failing = any(inp.oracle.is_failing() for inp in test_inputs)
        has_passing = any(not inp.oracle.is_failing() for inp in test_inputs)

        if not (has_failing and has_passing):
            raise ValueError("The initial inputs must contain at least one failing and one passing input.")


class FandangoRefinement(HypothesisInputFeatureDebugger):

    def __init__(
        self,
        grammar: Grammar,
        oracle: OracleType,
        initial_inputs: Union[Iterable[str], Iterable[FandangoInput]],
        max_iterations: int = 10,
        timeout_seconds: int = 3600,
        learner: Optional[FandangoLearner] = None,
        generator: Optional[Generator] = None,
        min_recall: float = 0.9,
        min_precision: float = 0.6,
        top_n_relevant_non_terminals: int = 3,
        relevant_non_terminals: Optional[Set[NonTerminal]] = None,
        logger_level: LoggerLevel = LoggerLevel.INFO,
        **kwargs,
    ):
        learner: FandangoLearner = (
            learner if learner else FandangoLearner(grammar, logger_level=logger_level)
        )
        generator: Generator = (
            generator if generator else FandangoGenerator(grammar)
        )
        self.engine: Engine = ParallelEngine(generator)

        super().__init__(
            grammar,
            oracle,
            initial_inputs,
            learner=learner,
            generator=generator,
            timeout_seconds=timeout_seconds,
            max_iterations=max_iterations,
            logger_level=logger_level,
            **kwargs,
        )
        self.max_candidates = 5
        self.relevant_non_terminals = relevant_non_terminals

    def learn_relevant_non_terminals(self):
        return self.relevant_non_terminals

    def learn_candidates(self, test_inputs: Set[FandangoInput]) -> Optional[List[FandangoConstraintCandidate]]:
        """
        Learn the candidates based on the test inputs. The candidates are ordered based on their scores.
        :param test_inputs: The test inputs to learn the candidates from.
        :return Optional[List[Candidate]]: The learned candidates.
        """
        LOGGER.info("Learning the candidates.")
        relevant_non_terminals = self.learn_relevant_non_terminals()

        _ = self.learner.learn_constraints(
            test_inputs, relevant_non_terminals=relevant_non_terminals
        )
        candidates = self.learner.get_best_candidates()
        return candidates[:self.max_candidates]

    def generate_test_inputs(self, candidates: List[FandangoConstraintCandidate]) -> Set[FandangoInput]:
        """
        Generate the test inputs based on the learned candidates.
        :param candidates: The learned candidates.
        :return Set[Input]: The generated test inputs.
        """
        LOGGER.info(f"Generating new test inputs for {len(candidates)} candidates.")
        test_inputs = self.engine.generate(candidates=candidates)
        return test_inputs

    def run_test_inputs(self, test_inputs: Set[FandangoInput]) -> Set[FandangoInput]:
        """
        Run the test inputs to label them. The test inputs are labeled based on the oracle.
        Feature vectors are assigned to the test inputs.
        :param test_inputs: The test inputs to run.
        :return Set[Input]: The labeled test inputs.
        """
        LOGGER.info(f"Running {len(test_inputs)} test inputs.")
        labeled_test_inputs = self.runner.label(test_inputs=test_inputs)
        return labeled_test_inputs


