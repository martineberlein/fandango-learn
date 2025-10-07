from typing import Any
from dataclasses import dataclass
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
    exp_log_level: LoggerLevel = LoggerLevel.DEBUG

    # Evaluation Strategies
    producer = False
    predictor = False

    # initial inputs generation
    generate_initial_inputs: bool = True
    num_positive_inputs: int = 50
    num_negative_inputs: int = 50


@dataclass
class RuleInductionSettings:
    pass


@dataclass
class FDLearnSettings:
    pass


@dataclass
class Result:
    experiment_settings: object = None
    tool_settings: object = None

    invariants: list[Any] = None
    runtime: float = 0.0

    # Run successful?
    success: bool = False