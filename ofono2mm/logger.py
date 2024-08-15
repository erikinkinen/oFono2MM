# Copyright (c) 2017-2024 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# Copyright (c) 2017 Bilal Elmoussaoui <bil.elmoussaoui@gmail.com>

import logging
import sys

class Logger:
    FORMAT = "[%(levelname)-s] %(message)s"
    __log = None
    APP = "ofono2mm"
    DEBUG = 0

    @staticmethod
    def get_default():
        if Logger.__log is None:
            logger = logging.getLogger(Logger.APP)

            handler = logging.StreamHandler(sys.stdout)
            formater = logging.Formatter(Logger.FORMAT, None)
            handler.setFormatter(formater)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)

            Logger.__log = logging.getLogger(Logger.APP)
        return Logger.__log

    @staticmethod
    def warning(msg, *args):
        Logger.get_default().warning(msg, *args)

    @staticmethod
    def debug(msg, *args):
        if Logger.DEBUG:
            Logger.get_default().debug(msg, *args)

    @staticmethod
    def info(msg, *args):
        Logger.get_default().info(msg, *args)

    @staticmethod
    def error(msg, *args):
        Logger.get_default().error(msg, *args)
