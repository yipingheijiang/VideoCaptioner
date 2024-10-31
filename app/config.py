import os
from pathlib import Path

VERSION = "0.1.0"
APP_NAME = "VideoCaptioner"
AUTHOR = "Weifeng"

# 路径
ROOT_PATH = Path(__file__).parent
CACHE_PATH = ROOT_PATH.parent / "cache"
LOG_PATH = ROOT_PATH.parent / "logs"
WORK_PATH = ROOT_PATH.parent.parent / "work-dir"

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
