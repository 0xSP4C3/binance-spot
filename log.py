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

if not os.path.exists("logging"):
    os.mkdir("logging")


def get_logger():
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


logger = get_logger()

if __name__ == "__main__":
    logger.info("this is info")
