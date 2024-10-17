import logging
import logging.handlers
import os

import urllib3
from urllib3.exceptions import InsecureRequestWarning


def setup_logger(name, level=logging.INFO,
                 fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'):
    """
    创建并配置一个日志记录器。

    参数：
    - name: 日志记录器的名称
    - level: 日志级别
    - fmt: 日志格式字符串
    """

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # logger.propagate = False  # 防止日志传播到父记录器

    # 如果记录器已经有处理器，避免重复添加
    if not logger.handlers:
        # 创建格式器
        formatter = logging.Formatter(fmt)

        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 设置特定库的日志级别
    for logger_name in ["urllib3", "requests", "openai", "httpx", "httpcore", "ssl", "certifi"]:
        logging.getLogger(logger_name).setLevel(logging.ERROR)

    return logger
