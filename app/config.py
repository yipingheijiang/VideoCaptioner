import os

VERSION = "0.1.0"
APP_NAME = "VideoCaptioner"
AUTHOR = "Weifeng"

#  路径
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(ROOT_PATH, "cache")
LOG_PATH = os.path.join(ROOT_PATH, "logs")

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
