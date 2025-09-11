import logging

def setup_logger(name="MedicalAssistant"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.hasHandlers():
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] --- [%(message)s]")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

logger = setup_logger()