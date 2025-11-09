import json
import logging
from enum import Enum, auto
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

class LogLevel(Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return 10 * (count + 1)
    DEBUG = auto()
    INFO = auto()
    WARN = auto()
    ERROR = auto()
    CRITICAL = auto()

    


class ColorFormatter(logging.Formatter):
    def __init__(self, mapping: dict[str,LogColors] = None, fmt = None, datefmt = None):
        super().__init__(fmt = fmt, datefmt = datefmt)
        self._colors = mapping 

    def format(self, record):
        color = (self._colors if self._colors is not None else Logger.__registry__).get(record.funcName, LogColors.DEFAULT) 
        record = super().format(record)
        return f'\033[38;5;{color.value}m{record}\033[0m'

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        return json.dumps({"datetime": datetime.fromtimestamp(record.created).strftime(self.datefmt),
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
        fh.setFormatter(JSONFormatter(datefmt = datefmt))
        logger.addHandler(fh)
    logger.addHandler(strm_hdlr)
    return logger
    
class Logger:
    __registry__ = {}
    def __init__(self,name, log_level = LogLevel.DEBUG,*,file_name = None, fh = False,
               format = "[%(asctime)s]: [%(levelname)s]: [%(funcName)s]: [%(lineno)d]: [%(msg)s]",
               datefmt = "%Y-%m-%d %I:%M:%S %p",filemode='a'):
        
        self.logger = logging.getLogger(name)
        self._cfg(log_level, file_name, fh, format, datefmt, filemode)

    def _cfg(self, log_level, file_name, fh, fmt, datefmt, filemode):
        def _cfg_hdlr(hdlr):
            hdlr.setLevel(log_level.value)
            hdlr.setFormatter(ColorFormatter(fmt = fmt, datefmt = datefmt) if hdlr.__class__ is logging.StreamHandler else JSONFormatter(datefmt = datefmt))
            self.logger.addHandler(hdlr)

        self.logger.setLevel(log_level.value)
        _cfg_hdlr(logging.StreamHandler())
        if fh:
            _cfg_hdlr(logging.FileHandler(filename = file_name, mode = filemode))
        
    def __getattr__(self, name):
        return getattr(self.logger,name)
    
    def register(self, color: LogColors|str|int):
        def dec(func):
            try:
                log_color = color if isinstance(color, LogColors) \
                    else (LogColors[color.upper()] if isinstance(color,str) else LogColors(color))
            except AttributeError as e:
                raise TypeError(f'LogColor should either be an enum of LogColors or str or int') from None 
            except (KeyError, ValueError) as e:
                raise ValueError(f'Invalid logcolor value should be on of {list(range(10,51,10))}' if isinstance(color, int) \
                                 else f'Invalid log color value should be one of {", ".join(x for x in dir(LogColors) if not x.startswith("_"))}') from e
            
            self.__registry__[func.__name__] = log_color

            return func
        return dec




