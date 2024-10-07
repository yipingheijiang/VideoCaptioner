# coding:utf-8
import sys
from enum import Enum

from PyQt5.QtCore import QLocale
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, RangeConfigItem, RangeValidator,
                            FolderListValidator, Theme, FolderValidator, ConfigSerializer, EnumSerializer, __version__)


class TranscribeModel(Enum):
    """ 转录模型 """
    JIANYING = "剪映"
    BIJIAN = "必剪"
    KUAISHOU = "快手"


class TargetLanguage(Enum):
    """ 目标语言 """
    CHINESE_SIMPLIFIED = "简体中文"
    CHINESE_TRADITIONAL = "繁体中文"
    ENGLISH = "英语"
    JAPANESE = "日语"
    KOREAN = "韩语"
    FRENCH = "法语"
    GERMAN = "德语"
    SPANISH = "西班牙语"
    ITALIAN = "意大利语"
    PORTUGUESE = "葡萄牙语"
    RUSSIAN = "俄语"
    TURKISH = "土耳其语"


class SubtitleStyle(Enum):
    """ 字幕样式 """
    DEFAULT = "默认"
    BOLD = "粗体"
    ITALIC = "斜体"
    UNDERLINE = "下划线"


class Language(Enum):
    """ 软件语言 """
    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Chinese, QLocale.HongKong)
    ENGLISH = QLocale(QLocale.English)
    AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO


class Config(QConfig):
    """ Config of application """
    # LLM CONFIG
    api_key = ConfigItem("LLM", "API_KEY", "")
    api_base = ConfigItem("LLM", "API_BASE", "https://api.openai.com/v1")
    model = ConfigItem("LLM", "MODEL", "gpt-4o")
    batch_size = RangeConfigItem("LLM", "BATCH_SIZE", 10, RangeValidator(10, 50))
    thread_num = RangeConfigItem("LLM", "THREAD_NUM", 10, RangeValidator(1, 50))

    # 转录配置
    transcribe_model = OptionsConfigItem("Transcribe", "Transcribe_MODEL", TranscribeModel.JIANYING.value,
                                         OptionsValidator(TranscribeModel), EnumSerializer(TranscribeModel))

    # 字幕配置
    subtitle_correct = ConfigItem("Subtitle", "Subtitle_CORRECT", True, BoolValidator())
    subtitle_translate = ConfigItem("Subtitle", "Subtitle_TRANSLATE", True, BoolValidator())
    subtitle_style = OptionsConfigItem("Subtitle", "Subtitle_STYLE", SubtitleStyle.DEFAULT.value, OptionsValidator(SubtitleStyle), EnumSerializer(SubtitleStyle))
    target_language = OptionsConfigItem("Subtitle", "TARGET_LANGUAGE", TargetLanguage.CHINESE_SIMPLIFIED.value,
                                        OptionsValidator(TargetLanguage), EnumSerializer(TargetLanguage))

    # 保存配置
    save_path = ConfigItem("Save", "SAVE_PATH", "app/download", FolderValidator())

    # main window
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", False, BoolValidator())
    dpiScale = OptionsConfigItem("MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem("MainWindow", "Language", Language.AUTO, OptionsValidator(Language), LanguageSerializer(), restart=True)

    # software update
    checkUpdateAtStartUp = ConfigItem("Update", "CheckUpdateAtStartUp", True, BoolValidator())


YEAR = 2024
AUTHOR = "BKFENG"
VERSION = __version__
HELP_URL = "https://www.bkfeng.top"

REPO_URL = "https://github.com/zhiyiYo/PyQt-Fluent-Widgets"
EXAMPLE_URL = "https://github.com/zhiyiYo/PyQt-Fluent-Widgets/tree/master/examples"
FEEDBACK_URL = "https://github.com/zhiyiYo/PyQt-Fluent-Widgets/issues"
RELEASE_URL = "https://github.com/zhiyiYo/PyQt-Fluent-Widgets/releases/latest"
SUPPORT_URL = "https://afdian.net/a/zhiyiYo"

cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load('app/config/config.json', cfg)
