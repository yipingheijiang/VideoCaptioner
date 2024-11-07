import logging
import logging.handlers
import os

import urllib3
from urllib3.exceptions import InsecureRequestWarning


def setup_logger(name: str, 
                level: int = logging.INFO,
                fmt: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                log_file: str = None) -> logging.Logger:
    """
    创建并配置一个日志记录器。

    参数：
    - name: 日志记录器的名称
    - level: 日志级别
    - fmt: 日志格式字符串
    - log_file: 日志文件路径
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(fmt)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 文件处理器，使用轮转策略
        if log_file:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    # 设置特定库的日志级别为ERROR以减少日志噪音
    error_loggers = ["urllib3", "requests", "openai", "httpx", "httpcore", "ssl", "certifi"]
    for lib in error_loggers:
        logging.getLogger(lib).setLevel(logging.ERROR)

    return logger