from typing import Any
from dataclasses import dataclass, field
import logging

from fdlearn.logger import LoggerLevel


EXP_LOGGER = logging.getLogger("experiment")
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s:%(levelname)s: %(message)s",
)


@dataclass
class Settings:
    seed: int = 42
    timeout: int = 60
    log_level: int = LoggerLevel.DEBUG
    exp_log_level: LoggerLevel = LoggerLevel.WARNING

    # Evaluation Strategies
    producer = False

    predictor = True
    eval_num_positive_inputs: int = 200
    eval_num_negatives_inputs: int = 200

    # initial inputs generation
    generate_initial_inputs: bool = True
    num_positive_inputs: int = 200
    num_negative_inputs: int = 100


@dataclass
class RuleInductionSettings:
    pass


@dataclass
class FDLearnSettings:
    pass
