# coding:utf-8
import sys
from enum import Enum

from PyQt5.QtCore import QLocale
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, RangeConfigItem, RangeValidator,
                            FolderListValidator, Theme, FolderValidator, ConfigSerializer, EnumSerializer, __version__)


from ..core.entities import TargetLanguageEnum, TranscribeModelEnum, OutputFormatEnum



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

class SubtitleLayoutEnum(Enum):
    """ 字幕布局 ["译文在上", "原文在上", "仅原文", "仅译文"]"""
    TRANSLATE_ON_TOP = "译文在上"
    ORIGINAL_ON_TOP = "原文在上"
    ONLY_ORIGINAL = "仅原文"
    ONLY_TRANSLATE = "仅译文"


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
    transcribe_model = OptionsConfigItem("Transcribe", "Transcribe_MODEL", TranscribeModelEnum.JIANYING.value,
                                         OptionsValidator(TranscribeModelEnum), EnumSerializer(TranscribeModelEnum))
    use_asr_cache = ConfigItem("Transcribe", "Use_ASR_Cache", True, BoolValidator())

    # 字幕配置
    need_optimize = ConfigItem("Subtitle", "Need_Optimize", True, BoolValidator())
    need_translate = ConfigItem("Subtitle", "Need_Translate", True, BoolValidator())
    # subtitle_style = OptionsConfigItem("Subtitle", "Subtitle_STYLE", SubtitleStyle.DEFAULT.value, OptionsValidator(SubtitleStyle), EnumSerializer(SubtitleStyle))
    target_language = OptionsConfigItem("Subtitle", "TARGET_LANGUAGE", TargetLanguageEnum.CHINESE_SIMPLIFIED.value,
                                        OptionsValidator(TargetLanguageEnum), EnumSerializer(TargetLanguageEnum))
    soft_subtitle = ConfigItem("Subtitle", "Soft_Subtitle", True, BoolValidator())
    # 字幕样式配置
    subtitle_style_name = ConfigItem("SubtitleStyle", "StyleName", "default")
    subtitle_layout = ConfigItem("SubtitleStyle", "Layout", "原文在上")
    subtitle_preview_image = ConfigItem("SubtitleStyle", "PreviewImage", "")

    # 保存配置
    work_dir = ConfigItem("Save", "Work_Dir", "app/work_dir", FolderValidator())

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
