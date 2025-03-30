import logging
import colorama
import sys
from typing import cast
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from pkgs import Data

colorama.init()

class LogRecordWithClassname(logging.LogRecord):
    classname: str

class ClassNameFilter(logging.Filter):
    def filter(self, record):
        """Adds class name to log record from instance or class"""
        record = cast(LogRecordWithClassname, record)
        record.classname = ""
        if hasattr(record, "__dict__"):
            if "self" in record.__dict__:
                record.classname = record.__dict__["self"].__class__.__name__
            elif "cls" in record.__dict__:
                record.classname = record.__dict__["cls"].__name__
            elif "classname" in record.__dict__:
                record.classname = record.__dict__["classname"]
        return True

class ColoredFormatter(logging.Formatter):
    """Custom formatter with granular color control"""
    time_color = colorama.Fore.BLUE
    reset = colorama.Style.RESET_ALL
    level_colors = {
        logging.DEBUG: colorama.Fore.CYAN,
        logging.INFO: colorama.Fore.GREEN,
        logging.WARNING: colorama.Fore.YELLOW,
        logging.ERROR: colorama.Fore.RED,
        logging.CRITICAL: colorama.Fore.MAGENTA + colorama.Style.BRIGHT,
    }

    def format(self, record):
        record = cast(LogRecordWithClassname, record)
        asctime = self.formatTime(record, self.datefmt)
        time_part = f"{self.time_color}[{asctime}]{self.reset}"
        
        module_part = f"{record.module}.{record.classname}.{record.funcName}"
        
        level_color = self.level_colors.get(record.levelno, colorama.Fore.WHITE)
        level_part = f"{level_color}[{record.levelname}]{self.reset}"
        arrow = f"{level_color}->{self.reset}"
        
        message = record.getMessage()

        if record.levelno >= logging.ERROR and record.exc_info is None:
            record.exc_info = sys.exc_info()
        
        formatted = (
            f"{time_part}: {level_part}: {module_part} {arrow} "
            f"{message}"
        )
        
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        if record.stack_info:
            formatted += "\n" + self.formatStack(record.stack_info)
            
        return formatted

class PlainFormatter(logging.Formatter):
    """Plain text formatter without colors"""
    def format(self, record):
        record = cast(LogRecordWithClassname, record)
        asctime = self.formatTime(record, self.datefmt)
        module_part = f"{record.module}.{record.classname}.{record.funcName}"
        level_part = f"[{record.levelname}]"
        message = record.getMessage()
        
        formatted = f"[{asctime}]: {level_part}: {module_part} -> {message}"
        
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        if record.stack_info:
            formatted += "\n" + self.formatStack(record.stack_info)
            
        return formatted

logger = logging.getLogger("ordraft")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    # Console handler with colored output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredFormatter(datefmt="%H:%M:%S"))
    logger.addHandler(console_handler)

    # File handler with plain text format and rotation
    if logger.level == logging.DEBUG:
        log_dir = "logs"
    elif logger.level == logging.INFO:
        log_dir = Data.data_path()

    os.makedirs(log_dir, exist_ok=True)
    current_date = datetime.now().strftime("%Y%m%d")
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, f"ordraft_{current_date}.log"),
        maxBytes=10*1024*1024,  # 10MB max file size
        backupCount=5,  # Keep 5 backup files
        encoding='utf-8'
    )
    file_handler.setFormatter(PlainFormatter(datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(file_handler)

    logger.addFilter(ClassNameFilter())

__all__ = ["logger"]

if __name__ == "__main__":
    logger.debug("Debug message")
    logger.info("Information message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
