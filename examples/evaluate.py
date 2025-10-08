import random
from time import time

from examples.results import Result, print_results_table, ResultInvariant
from examples.subjects.bug.middle.middle import get_middle_subject
from examples.subjects.valid.iban.iban_evaluation import get_iban_subject
from subjects.bug.calculator.calculator_evaluation import get_calculator_subject
from examples.subjects.subject import Subject
from examples.subjects.valid.heartbeat.heartbeat_evaluation import get_heartbeat_subject
from fdlearn.data import FandangoInput, OracleResult
from subjects.valid.xml.xml_evaluation import get_xml_subject

from fdlearn.learner import FandangoLearner
from fdlearn.learning.rule_induction.rule_induction import RuleInductionLearner
from fdlearn.core import BaseFandangoLearner

from settings import (
    Settings,
    RuleInductionSettings,
    FDLearnSettings,
    EXP_LOGGER,
)


def generate_initial_inputs(
    subject: Subject, min_positives, min_negatives
) -> tuple[set[FandangoInput], set[FandangoInput]]:

    positive, negative = set(), set()
    while (
        len(positive) < min_positives
        or len(negative) < min_negatives
    ):
        tree = subject.grammar.fuzz()
        inp = tree.to_string()
        if subject.oracle(inp).is_failing():
            if len(positive) < min_positives:
                positive.add(FandangoInput(tree=tree, oracle=OracleResult.FAILING))
        else:
            if len(negative) < min_negatives:
                negative.add(FandangoInput(tree=tree, oracle=OracleResult.PASSING))

    EXP_LOGGER.debug(
        f"Generated {len(positive)} positive inputs and {len(negative)} negative inputs."
    )
    return positive, negative


def evaluate_predictor(result: Result, exp_config: Settings, evaluation_inputs: set[FandangoInput]):
    if not (result.success and exp_config.predictor):
        return

    positives = [inp for inp in evaluation_inputs if inp.oracle == OracleResult.FAILING]
    negatives = [inp for inp in evaluation_inputs if inp.oracle == OracleResult.PASSING]

    for result_inv in result.invariants:
        for inp in evaluation_inputs:
            if inp.oracle.is_failing() != result_inv.invariant.check(inp):
                print(inp, inp.oracle, result_inv.invariant.check(inp))
        result_inv.tp = sum(result_inv.invariant.check(inp) for inp in positives)
        result_inv.fn = len(positives) - result_inv.tp
        result_inv.fp = sum(result_inv.invariant.check(inp) for inp in negatives)
        result_inv.tn = len(negatives) - result_inv.fp


def run_tool(
    tool: type[BaseFandangoLearner],
    subject: Subject,
    settings,
    experiment_settings,
    result: Result,
):
    start_time = time()

    try:
        invariants = tool(grammar=subject.grammar, **vars(settings)).learn_constraints(
            test_inputs=subject.initial_inputs,
            # relevant_non_terminals={NonTerminal("<x>"), NonTerminal("<y>"), NonTerminal("<z>")}
        )
        result.runtime = time() - start_time

        for invariant in invariants:
            result.invariants.append(
                ResultInvariant(
                    invariant=invariant
                )
            )
        result.success = True
    except Exception as e:
        result.success = False


def evaluate(subjects, tools):
    exp_config = Settings()
    random.seed(exp_config.seed)

    EXP_LOGGER.setLevel(exp_config.exp_log_level.value)

    results = []
    for subject in subjects:
        subject_data = subject()
        EXP_LOGGER.info(f"Evaluating: {subject_data.name}")

        if exp_config.generate_initial_inputs:
            positive_inputs, negative_inputs = generate_initial_inputs(
                subject_data, exp_config.num_positive_inputs, exp_config.num_negative_inputs
            )
            subject_data.initial_inputs = positive_inputs.union(negative_inputs)

        evaluation_inputs = []
        if exp_config.predictor:
            positive_inputs, negative_inputs = generate_initial_inputs(
                subject_data, exp_config.eval_num_positive_inputs, exp_config.eval_num_negatives_inputs
            )
            evaluation_inputs = positive_inputs.union(negative_inputs)

        for name, tool, config in tools:
            result = Result(tool_name=name, subject_name=subject_data.name)
            result.experiment_settings = exp_config
            result.tool_settings = config

            run_tool(tool, subject_data, config, exp_config, result)

            evaluate_predictor(result, exp_config, evaluation_inputs)
            results.append(result)
            print(result.invariants)

    print_results_table(results)

            # solutions = run_evaluation(subject_data, seconds=60)
            # results = evaluate_generated_inputs(subject_data, solutions)
            # row_print_averages(results, write_to_file=False)


if __name__ == "__main__":
    subjects_ = [
        get_iban_subject,
        get_middle_subject,
        get_calculator_subject,
        get_xml_subject,
        get_heartbeat_subject,
    ]

    tools_ = [
        ("RDLearn", RuleInductionLearner, RuleInductionSettings()),
        ("FDLearn", FandangoLearner, FDLearnSettings()),
    ]

    evaluate(subjects_, tools_)
