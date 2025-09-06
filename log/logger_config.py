import logging
import time
from logging.handlers import TimedRotatingFileHandler

# Configure logging

def logger_config():
    logger = logging.getLogger("ib-flask") # logging.getLogger(__name__)
    log_format = '%(message)s'
    handler = logging.StreamHandler()
    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    log_file = f"IBFlask_{str(int(time.time()))}.txt"
    formatter = logging.Formatter('%(message)s')
    handler = TimedRotatingFileHandler(log_file, when='h', interval=1)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.setLevel(logging.INFO)
    return logger

def get_log_messages():
    pass