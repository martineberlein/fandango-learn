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
    seed: int = 0 # 42
    timeout: int = 60
    log_level: int = LoggerLevel.DEBUG
    exp_log_level: LoggerLevel = LoggerLevel.DEBUG

    # Evaluation Strategies
    producer = False

    predictor = False
    eval_num_positive_inputs: int = 100
    eval_num_negatives_inputs: int = 100

    # initial inputs generation
    generate_initial_inputs: bool = True
    num_positive_inputs: int = 100
    num_negative_inputs: int = 100


@dataclass
class RuleInductionSettings:
    logger_level: LoggerLevel = LoggerLevel.DEBUG
    min_recall: float = 0.9

@dataclass
class FDLearnSettings:
    logger_level: LoggerLevel = LoggerLevel.INFO
