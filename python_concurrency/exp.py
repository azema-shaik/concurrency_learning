import logging
from experiments.logger import JSONFormatter as JsonLogger


logger = logging.getLogger("name")
logger.setLevel(logging.DEBUG)
strm_hdlr = logging.StreamHandler()
strm_hdlr.setLevel(logging.DEBUG)
strm_hdlr.setFormatter(JsonLogger())
logger.addHandler(strm_hdlr)
logger.error({"a":"b"})
logger.error({"a":"b"})