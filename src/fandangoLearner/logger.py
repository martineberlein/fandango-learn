import logging
import enum


LOGGER = logging.getLogger("fandango-learner")
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s:%(levelname)s: %(message)s",
)


class LoggerLevel(enum.Enum):
    NOTSET = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
