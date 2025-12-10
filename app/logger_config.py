import logging
import sys
from logging import Logger

def setup_logger() -> Logger:
    logger = logging.getLogger("ai_engine")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers on repeated imports
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    fh = logging.FileHandler("ai_engine.log")
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger

logger = setup_logger()
