from loguru import logger
import sys

grey = "\x1b[38;20m"
yellow = "\x1b[33;20m"
red = "\x1b[31;20m"
bold_red = "\x1b[31;1m"
reset = "\x1b[0m"

def setup():
  logger.remove()
  logger.level("INFO", color="<white>")
  logger.level("DEBUG", color="<green>")
  logger.level("WARNING", color="<yellow>")
  logger.level("ERROR", color="<red>")
  logger.level("CRITICAL", color="<b><l><red>")
  logger.add(sink=sys.stdout, format="<blue><bold>{time:YYYY-MM-DD at HH:mm:ss}</></> - <green>{name}.py</> - <level>{level}</level>: {message}", colorize=True, backtrace=True, enqueue=True)
  return logger