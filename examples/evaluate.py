import random
from time import time

from examples.subjects.bug.middle.middle import get_middle_subject
from subjects.bug.calculator.calculator_evaluation import get_calculator_subject
from examples.subjects.subject import Subject
from examples.subjects.valid.heartbeat.heartbeat_evaluation import get_heartbeat_subject
from fdlearn.data import FandangoInput, OracleResult
from subjects.valid.xml.xml_evaluation import get_xml_subject

from fdlearn.learner import FandangoLearner
from fdlearn.learning.rule_induction.rule_induction import RuleInductionLearner
from fdlearn.core import BaseFandangoLearner

from settings import Settings, RuleInductionSettings, FDLearnSettings, EXP_LOGGER, Result


def generate_initial_inputs(subject: Subject, experiment_settings: Settings) -> tuple[set[FandangoInput], set[FandangoInput]]:

    positive, negative = set(), set()
    while len(positive) < experiment_settings.num_positive_inputs or len(negative) < experiment_settings.num_negative_inputs:
        tree = subject.grammar.fuzz()
        inp = tree.to_string()
        if subject.oracle(inp).is_failing():
            if len(positive) < experiment_settings.num_positive_inputs:
                positive.add(FandangoInput(tree=tree, oracle=OracleResult.FAILING))
        else:
            if len(negative) < experiment_settings.num_negative_inputs:
                negative.add(FandangoInput(tree=tree, oracle=OracleResult.PASSING))

    EXP_LOGGER.debug(f"Generated {len(positive)} positive inputs and {len(negative)} negative inputs.")
    return positive, negative


def run_tool(tool: type[BaseFandangoLearner], subject: Subject, settings, experiment_settings, result: Result):
    start_time = time()

    try:
        invariants = tool(
            grammar=subject.grammar,
            **vars(settings)
        ).learn_constraints(
            test_inputs=subject.initial_inputs
        )
        result.runtime = time() - start_time
        result.invariants = invariants
        result.success = True
    except Exception as e:
        result.success = False


def evaluate(subjects, tools):
    exp_config = Settings()
    random.seed(exp_config.seed)

    EXP_LOGGER.setLevel(exp_config.exp_log_level.value)

    for subject in subjects:
        subject_data = subject()

        if exp_config.generate_initial_inputs:
            positive_inputs, negative_inputs = generate_initial_inputs(subject_data, exp_config)
            subject_data.initial_inputs = positive_inputs.union(negative_inputs)

        if exp_config.predictor:
            positive_inputs, negative_inputs = generate_initial_inputs(subject_data, exp_config)
            evaluation_inputs = positive_inputs.union(negative_inputs)

        for tool, config in tools:
            result = Result()
            result.experiment_settings = exp_config
            result.tool_settings = config

            run_tool(tool, subject_data, config, exp_config, result)
            print(result.invariants)
            print(result.runtime)

            # solutions = run_evaluation(subject_data, seconds=60)
            # results = evaluate_generated_inputs(subject_data, solutions)
            # row_print_averages(results, write_to_file=False)


if __name__ == "__main__":
    subjects_ = [
        get_middle_subject,
        get_calculator_subject,
        get_xml_subject,
        get_heartbeat_subject,
    ]

    tools_ = [
        (RuleInductionLearner, RuleInductionSettings()),
        (FandangoLearner, FDLearnSettings())
    ]

    evaluate(subjects_, tools_)
