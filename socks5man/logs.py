from __future__ import absolute_import
import copy
import logging
import sys

from socks5man.misc import cwd, yellow, red

class ConsoleHandler(logging.StreamHandler):
    """Logging to console handler."""

    def emit(self, record):
        colored = copy.copy(record)
        if record.levelname == "WARNING":
            colored.msg = yellow(record.msg)
        elif record.levelname == "ERROR" or record.levelname == "CRITICAL":
            colored.msg = red(record.msg)

        logging.StreamHandler.emit(self, colored)

def init_loggers(level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )
    # create a file handler
    fhandler = logging.FileHandler(cwd("socks5man.log"))

    fhandler.setFormatter(fmt)
    logger.addHandler(fhandler)

    shandler = ConsoleHandler(sys.stdout)
    shandler.setFormatter(fmt)
    logger.addHandler(shandler)
