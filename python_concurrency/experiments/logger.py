import json
import logging
from enum import Enum
from datetime import datetime


class LogColors(Enum):
    RED = 9
    CYAN = 14 
    PURPLE = 5
    PINK = 13
    YELLOW = 11
    GREEN = 10
    DARK_BLUE = 4
    TURQUOISE = 6
    DEFAULT = 15


class ColorFormatter(logging.Formatter):
    def __init__(self, mapping: dict[str,LogColors], fmt = None, datefmt = None):
        super().__init__(fmt = fmt, datefmt = datefmt)
        self._colors = mapping 

    def format(self, record):
        color = self._colors.get(record.funcName, LogColors.DEFAULT)
        record = super().format(record)
        return f'\033[38;5;{color.value}m{record}\033[0m'

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        return json.dumps({"datetime": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %I:%M:%S %f %p"),
                "level":record.levelname, "func_name": record.funcName, "lineno": record.lineno,
                "filename": record.filename,"msg":record.msg} )

def get_logger(name,color_mapping, *, file_name, fh = False,
               format = "[%(asctime)s]: [%(levelname)s]: [%(funcName)s]: [%(lineno)d]: [%(msg)s]",
               datefmt = "%Y-%m-%d %I:%M:%S %p",filemode='a'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    strm_hdlr = logging.StreamHandler()
    strm_hdlr.setLevel(logging.DEBUG)
    strm_hdlr.setFormatter(ColorFormatter(mapping = color_mapping, fmt = format, datefmt = datefmt))
    if fh:
        fh = logging.FileHandler(filename = file_name, mode = filemode)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(JSONFormatter())
        logger.addHandler(fh)
    logger.addHandler(strm_hdlr)
    return logger
    

