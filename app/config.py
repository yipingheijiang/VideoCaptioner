import os
from pathlib import Path

VERSION = "1.0.0"
YEAR = 2024
APP_NAME = "VideoCaptioner"
AUTHOR = "Weifeng"

HELP_URL = "https://www.bkfeng.top"
GITHUB_REPO_URL = "https://github.com/WEIFENG2333/VideoCaptioner"
RELEASE_URL = "https://github.com/WEIFENG2333/VideoCaptioner/releases/latest"
FEEDBACK_URL = "https://github.com/WEIFENG2333/VideoCaptioner/issues"

# 路径
ROOT_PATH = Path(__file__).parent

RESOURCE_PATH = ROOT_PATH / "resource"
APPDATA_PATH = ROOT_PATH.parent / "AppData"

BIN_PATH = RESOURCE_PATH / "bin"
ASSETS_PATH = RESOURCE_PATH / "assets"


CACHE_PATH = APPDATA_PATH / "cache"
LOG_PATH = APPDATA_PATH / "logs"
SETTINGS_PATH = APPDATA_PATH / "settings.json"
WORK_PATH = APPDATA_PATH / "work-dir"
MODEL_PATH = APPDATA_PATH / "models"

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 环境变量添加 bin 路径
os.environ["PATH"] = os.environ["PATH"] + os.pathsep + str(BIN_PATH)
