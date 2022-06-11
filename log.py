# !/usr/bin/python3
# -*- coding: utf-8 -*-
# Auth0r: ara_umi
# Email: 532990165@qq.com
# DateTime: 2022/6/5 16:15

import os
import time
from logging.handlers import TimedRotatingFileHandler

import logging

from settings import LOG_LEVEL


class Logger(object):
    def __init__(self):
        self.logger = self._logger_init()

    @staticmethod
    def _mkdir():
        if not os.path.exists("logging"):
            os.mkdir("logging")

    def _logger_init(self):
        """
        logger options
        """
        self._mkdir()

        logger = logging.getLogger()
        logger.setLevel(LOG_LEVEL)
        BASIC_FORMAT = "%(asctime)s:%(levelname)s:%(message)s"
        DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(BASIC_FORMAT, DATE_FORMAT)

        chlr = logging.StreamHandler()  # 输出到控制台的handler
        chlr.setFormatter(formatter)
        chlr.setLevel("INFO")  # 也可以不设置，不设置就默认用logger的level

        filename = f'{time.strftime("%Y%m%d%H%M%S")}.log'
        fhlr = TimedRotatingFileHandler(f"./logging/{filename}", when="H", interval=6,
                                        backupCount=10)

        fhlr.setFormatter(formatter)

        logger.addHandler(chlr)
        logger.addHandler(fhlr)

        return logger

    def get_logger(self):
        """
        get logger
        """
        self.logger.info("Logger get")
        return self.logger


if __name__ == "__main__":
    my_logger = Logger().get_logger()
    my_logger.info("this is info")
