from logging import StreamHandler
from logging.handlers import RotatingFileHandler

import logging
import os
import sys


class LogFactory:
    """
    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0
    """

    logging_levels = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "SILLY": 5,
        "NOTSET": logging.NOTSET,
    }
    format = "%(asctime)s | %(levelname)s | %(pathname)s | %(process)d | %(processName)s | \
                %(filename)s | %(funcName)s | %(lineno)d | %(name)s | %(message)s |"
    datefmt = "%d-%b-%y %H:%M:%S"
    log_file_name = "logs/starter_service.log"

    @classmethod
    def configure_logger(cls, logger_name=None, logging_level=None):
        # Initializing logger
        logger = (
            logging.getLogger(name=logger_name) if logger_name else logging.getLogger()
        )
        if logging_level not in LogFactory.logging_levels:
            logging_level = "WARN"
        logger.setLevel(logging_level)

        # Defining handlers
        os.makedirs(os.path.dirname(cls.log_file_name), exist_ok=True)
        file_handler = RotatingFileHandler(
            cls.log_file_name,
            maxBytes=1048576,
            backupCount=5,
            encoding="utf-8",
        )
        std_out_handler = StreamHandler(stream=sys.stdout)

        # Defining the formatter
        formatter = logging.Formatter(fmt=cls.format, datefmt=cls.datefmt)

        # Adding formatter to handlers
        file_handler.setFormatter(formatter)
        std_out_handler.setFormatter(formatter)

        # Adding handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(std_out_handler)
        logger.debug("Configured the logger")


logger_name = "starter_service_logger"
