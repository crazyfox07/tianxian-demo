# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: log.py
@time: 2020/9/1 8:35
"""
import logging
import os
from common.utils import CommonUtil
from common.config import CommonConf

class Logger:
    def __init__(self, logame, logfile):
        """
        日志
        :param logame: log对象名
        :param logfile: 生成log文件路径
        """
        self.logger = logging.getLogger(logame)
        # 创建一个handler，用于写入日志文件
        file_handler = logging.FileHandler(logfile, mode='a')
        # 再创建一个handler, 用于输出到控制台
        console_handler = logging.StreamHandler()
        # 定义handler的输出格式
        formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        # 添加handler
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        # 设置日志级别
        self.logger.setLevel(logging.INFO)


os.makedirs(CommonConf.LOG_DIR, exist_ok=True)
log_path = os.path.join(CommonConf.LOG_DIR, CommonUtil.timestamp_format(format="%Y%m%d")+'-tianxian.log')

logger = Logger("tianxian", log_path).logger


if __name__ == "__main__":
    logger.info("222222222222222")
    logger.error("333333333333333")
