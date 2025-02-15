# logs.py
import os
from loguru import logger

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "jobs_applier.log")

logger.add(LOG_FILE, rotation="5 MB", backtrace=True, diagnose=True)

def get_logger(name: str):
    """
    Returns a Loguru logger with a specific context.
    """
    return logger.bind(module=name)
