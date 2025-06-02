import os
from pathlib import Path

from debugging_benchmark.calculator.calculator import CalculatorBenchmarkRepository
from debugging_benchmark.expression.expression import ExpressionBenchmarkRepository
from debugging_benchmark.middle.middle import MiddleBenchmarkRepository
from debugging_benchmark.markup.markup import MarkupBenchmarkRepository as MarkUpBenchmarkRepository
from debugging_benchmark.tests4py_benchmark.repository import (
    PysnooperBenchmarkRepository,
    CookiecutterBenchmarkRepository,
)
from debugging_benchmark.heartbleed.heartbleed import HeartbleedBenchmarkRepository

from dbg.logger import LoggerLevel
from evaluation_dbg.base_experiment import FDLearnRefinementExperiment

from fdlearn.data.oracle import OracleResult
from fdlearn.interface.fandango import parse
from fdlearn.refinement.core import FandangoRefinement

def create_alhazen_experiment(name, repository_cls, program_index=0, custom_inputs_func=None, print_inputs=True):
    programs = repository_cls().build()
    program = programs[program_index]

    dirname = os.path.dirname(__file__)
    filename = os.path.join(Path(dirname).parent / f"grammars/{name}.fan")
    grammar, _ = parse(filename)


    def oracle(x):
        result_ = program.oracle(x)
        result = result_[0] if isinstance(result_, (list, tuple)) else result_
        if result.is_failing():
            return OracleResult.FAILING
        if str(result) == "UNDEFINED":
            return OracleResult.UNDEFINED
        return OracleResult.PASSING

    if custom_inputs_func:
        initial_inputs = set(custom_inputs_func(program))
    else:
        initial_inputs = set(program.get_initial_inputs())

    if print_inputs:
        for inp in initial_inputs:
            print(inp, oracle(inp))

    refinement = FandangoRefinement(
        grammar=grammar,
        initial_inputs=initial_inputs,
        oracle=oracle,
        #logger_level=LoggerLevel.CRITICAL,
    )

    return FDLearnRefinementExperiment(
        name=name,
        subject_name=name,
        tool=refinement,
        grammar=grammar,
        initial_inputs=initial_inputs,
        oracle=oracle,
    )


# Experiment getters using the helper
def get_calculator_experiment():
    return create_alhazen_experiment("Calculator", CalculatorBenchmarkRepository)

def get_heartbleed_experiment():
    return create_alhazen_experiment("Heartbleed", HeartbleedBenchmarkRepository)

def get_expression_experiment():
    return create_alhazen_experiment("Expression", ExpressionBenchmarkRepository)

def get_middle_experiment():
    return create_alhazen_experiment("Middle", MiddleBenchmarkRepository)

def get_markup1_experiment():
    return create_alhazen_experiment("Markup1", MarkUpBenchmarkRepository)

def get_markup2_experiment():
    return create_alhazen_experiment("Markup2", MarkUpBenchmarkRepository, program_index=1)

def get_pysnooper1_experiment():
    return create_alhazen_experiment(
        "Pysnooper1",
        PysnooperBenchmarkRepository,
        custom_inputs_func=lambda p: p.get_passing_inputs()[:2] + p.get_failing_inputs()[:1],
        print_inputs=True
    )

def get_pysnooper2_experiment():
    return create_alhazen_experiment(
        "Pysnooper2",
        PysnooperBenchmarkRepository,
        program_index=1,
        custom_inputs_func=lambda p: p.get_passing_inputs()[:2] + p.get_failing_inputs()[:1]
    )

def get_cookiecutter1_experiment():
    return create_alhazen_experiment(
        "Cookiecutter1",
        CookiecutterBenchmarkRepository,
        custom_inputs_func=lambda p: p.get_passing_inputs()[:2] + p.get_failing_inputs()[:1]
    )

def get_cookiecutter2_experiment():
    return create_alhazen_experiment(
        "Cookiecutter2",
        CookiecutterBenchmarkRepository,
        program_index=1,
        custom_inputs_func=lambda p: p.get_passing_inputs()[:2] + p.get_failing_inputs()[:1]
    )


if __name__ == "__main__":
    from fdlearn.learning.candidate import FandangoConstraintCandidate
    from fdlearn.learner import ValueMaps, FandangoLearner, PatternProcessor, ConjunctionProcessor, FandangoInput
    from fandango.constraints.base import GeneticBase
    from fandango.constraints.base import Constraint
    from evaluation_dbg.util import instrument_classes, write_timings_to_csv, write_summary_to_csv, log_runtime
    instrument_classes([GeneticBase, FandangoRefinement,FandangoLearner, PatternProcessor, ConjunctionProcessor, FandangoInput, FandangoConstraintCandidate, ValueMaps], log_runtime)


    experiments = [
        # get_calculator_experiment,
        # get_heartbleed_experiment,
        # get_expression_experiment,
        # get_middle_experiment,
        # get_markup1_experiment,
        # get_markup2_experiment,
        get_pysnooper1_experiment,
        # get_pysnooper2_experiment,
        # get_cookiecutter1_experiment,
        # get_cookiecutter2_experiment,
    ]

    for experiment in experiments:
        exp = experiment().evaluate()

        #write_timings_to_csv(f"{exp['name']}_method_timings.csv")
        write_summary_to_csv(f"{exp['name']}_method_timings_summary.csv")

        print(f"Experiment: {exp['name']}")
        print(f"Time: {exp['time_in_seconds']} seconds")
        for candidate in exp["candidates"]:
            print(candidate)
