import random
import time
from abc import abstractmethod
from typing import Optional

from fdlearn.interface.fandango import Grammar
from fdlearn.data.input import FandangoInput
from fdlearn.learner import FandangoLearner

from dbg_evaluation.experiment import Experiment, format_results
from dbg.data.oracle import OracleResult

from fdlearn.reduction.feature_collector import GrammarFeatureCollector
from fdlearn.reduction.reducer import FeatureReducer
from fdlearn.refinement.core import FandangoRefinement


class FDLearnExperiment(Experiment):

    @abstractmethod
    def evaluate(self, seed = 1, **kwargs):
        raise NotImplementedError()

    def _prepare_inputs(self, inputs: set[str]) -> set[FandangoInput]:
        parsed = {
            FandangoInput.from_str(self.grammar, inp, self.oracle(inp))
            for inp in inputs
        }
        return parsed

    def get_evaluation_inputs(self, num_inputs: int = 2000) -> set[FandangoInput]:
        """
        Get evaluation inputs from disk or generate them using a grammar fuzzer.
        """
        inputs = self._load_or_generate_inputs(num_inputs)

        parsed = {
            FandangoInput.from_str(self.grammar, inp, result)
            for inp, result in inputs
        }

        return parsed

    def _load_or_generate_inputs(self, num_inputs: int) -> list[tuple[str, bool]]:
        inputs = self.load_evaluation_inputs()
        if inputs:
            return inputs

        print("No inputs loaded; generating new evaluation inputs.")
        inputs = self._generate_inputs(num_inputs)
        self.write_to_file(
            {
                FandangoInput.from_str(self.grammar, inp, result)
                for inp, result in inputs
            },
            self.subject_name,
        )
        return inputs

    def _generate_inputs(self, num_inputs: int) -> list[tuple[str, bool]]:
        inputs = []
        random.seed(1)

        assert isinstance(self.grammar, Grammar)

        while len(inputs) < num_inputs:
            tree = self.grammar.fuzz()
            inp = tree.to_string()
            result = self.oracle(inp)
            if result != OracleResult.UNDEFINED:
                inputs.append((inp, result.is_failing()))

        return inputs

    def load_evaluation_inputs(self) -> list[tuple[str, bool]]:
        """
        Attempt to load inputs from disk. Returns an empty list if loading fails.
        """
        try:
            inputs = self.load()
            print(f"Loaded {len(inputs)} inputs")
            return inputs
        except Exception as e:
            print(f"Error loading inputs: {e}")
            return []


class LearnerExperiment(FDLearnExperiment):
    def evaluate(self, seed: int = 1, **kwargs):
        """Evaluate the learner and return formatted results."""
        random.seed(seed)

        parsed_inputs = self._prepare_inputs(self.initial_inputs)
        for inp in parsed_inputs:
            print(inp, inp.oracle)

        assert isinstance(self.tool, FandangoLearner)

        start_time = time.time()
        explanations = self.tool.learn_constraints(test_inputs=parsed_inputs, oracle=self.oracle) # learn_explanation(test_inputs=parsed_inputs, seed=seed, **kwargs)
        duration = round(time.time() - start_time, 4)

        return format_results(
            self.name, explanations, duration, self.evaluation_inputs, seed=seed
        )


class ReducerExperiment(FDLearnExperiment):

    def _prepare_inputs(self, inputs: set[str]) -> set[FandangoInput]:
        parsed = {
            FandangoInput.from_str(self.grammar, inp, self.oracle(inp))
            for inp in inputs
        }

        for inp in parsed:
            inp.features = GrammarFeatureCollector(self.grammar).collect_features(inp)

        return parsed

    def evaluate(self, seed = 1, **kwargs):
        random.seed(seed)

        test_inputs = {str(self.grammar.fuzz()) for _ in range(50)}
        parsed_inputs = self._prepare_inputs(self.initial_inputs.union(test_inputs))
        assert isinstance(self.tool, FeatureReducer)

        start_time = time.time()
        relevant_features = self.tool.learn(test_inputs=parsed_inputs)
        duration = round(time.time() - start_time, 4)

        relevant_features_non_terminals = {
            feature.non_terminal for feature in relevant_features
        }

        print(relevant_features_non_terminals)
        print(duration)

        start_time = time.time()
        learner = FandangoLearner(self.grammar)
        explanations = learner.learn_constraints(test_inputs=parsed_inputs, oracle=self.oracle, relevant_non_terminals=relevant_features_non_terminals)
        duration = round(time.time() - start_time, 4)

        return format_results(
            self.name, explanations, duration, self.evaluation_inputs, seed=seed
        )


class FDLearnRefinementExperiment(FDLearnExperiment):

    def evaluate(self, seed = 1, **kwargs):
        random.seed(seed)

        assert isinstance(self.tool, FandangoRefinement)

        start_time = time.time()
        explanations = self.tool.explain()
        duration = round(time.time() - start_time, 4)

        return format_results(
            self.name, explanations, duration, self.evaluation_inputs, seed=seed
        )