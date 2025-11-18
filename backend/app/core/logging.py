from loguru import logger
import sys

# Basic Loguru setup; can be extended to JSON/structured logs as needed
logger.remove()
logger.add(sys.stdout, level="INFO", backtrace=False, diagnose=False)

__all__ = ["logger"]
