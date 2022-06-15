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


class Singleton(object):
    __instance = None

    # make sure there's only one logger
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance


class MyLogger(Singleton):
    __init_flag = False

    def __init__(self):
        if not self.__init_flag:
            self.__init_flag = True
            self._mkdir()
            self._logger = self._logger_init()

    @property
    def logger(self):
        return self._logger

    @staticmethod
    def _mkdir():
        # mkdir for log files
        if not os.path.exists("logging"):
            os.mkdir("logging")

    def _logger_init(self):
        """
        logger options
        """

        logger = logging.getLogger()
        logger.setLevel(LOG_LEVEL)
        BASIC_FORMAT = "%(asctime)s:%(levelname)s:%(message)s"
        DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(BASIC_FORMAT, DATE_FORMAT)

        chlr = logging.StreamHandler()
        chlr.setFormatter(formatter)
        chlr.setLevel("INFO")  # 也可以不设置，不设置就默认用logger的level

        filename = f'{time.strftime("%Y%m%d%H%M%S")}.log'
        fhlr = TimedRotatingFileHandler(f"./logging/{filename}", when="H", interval=6,
                                        backupCount=10)

        fhlr.setFormatter(formatter)

        logger.addHandler(chlr)
        logger.addHandler(fhlr)

        return logger


if __name__ == "__main__":
    my_logger = MyLogger().get_logger()
    my_logger.info("this is info")
